"""
Data synchronization service for fetching Planning Center data and loading to SQL Server.
Adapted from planning_center_new.py for multi-tenant use.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.etl.pco_client import PCOClient
from app.etl.metadata_discovery import MetadataDiscovery
from app.etl.data_processor import (
    process_jsonapi_response,
    convert_timestamps_to_timezone,
    add_derived_date_columns,
    prepare_dataframe_for_sql,
    generate_dtype_mapping,
)
from app.security import decrypt_credential
from app.models import Tenant, DataRefreshJob
from app.database import engine

logger = logging.getLogger(__name__)


def parse_event_time_ids(val):
    """Parse event_time_ids which can be JSON string, list, or single value."""
    if isinstance(val, list):
        return val
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return []
    if isinstance(val, str):
        val_stripped = val.strip()
        if not val_stripped:
            return []
        # Check if it's a JSON string
        if (val_stripped.startswith('[') and val_stripped.endswith(']')) or \
           (val_stripped.startswith('"') and val_stripped.endswith('"')):
            try:
                parsed = json.loads(val_stripped)
                return parsed if isinstance(parsed, list) else [parsed] if parsed else []
            except:
                pass
        # Try to convert string representation of list
        try:
            import ast
            parsed = ast.literal_eval(val_stripped)
            return parsed if isinstance(parsed, list) else [parsed] if parsed else []
        except:
            # Might be a single ID value
            try:
                return [int(val_stripped)] if val_stripped.isdigit() else [val_stripped]
            except:
                return []
    # Try to convert to list if it's a single value
    try:
        return [val]
    except:
        return []


class DataSyncService:
    """Service for synchronizing Planning Center data for a tenant."""

    # Endpoints to fetch for the dashboard (simplified from full discovery)
    DASHBOARD_ENDPOINTS = {
        'people': {
            'endpoint': '/people/v2/people',
            'includes': ['emails', 'phone_numbers'],
            'table_name': 'PC_PEOPLE'
        },
        'check_ins': {
            'endpoint': '/check-ins/v2/check_ins',
            'includes': ['event_times', 'locations', 'person'],
            'table_name': 'PC_CHECKINS'
        },
        'events': {
            'endpoint': '/check-ins/v2/events',
            'includes': [],
            'table_name': 'PC_EVENTS'
        },
        'event_times': {
            'endpoint': '/check-ins/v2/event_times',
            'includes': ['event'],
            'table_name': 'PC_EVENT_TIMES'
        }
    }

    def __init__(self, tenant: Tenant, job: DataRefreshJob, db: Session):
        """
        Initialize sync service.

        Args:
            tenant: Tenant to sync data for
            job: DataRefreshJob to track progress
            db: Database session
        """
        self.tenant = tenant
        self.job = job
        self.db = db
        self.schema_name = tenant.schema_name  # SQL schema name (e.g., gf_paradise_tx)
        self.client: Optional[PCOClient] = None
        self.dataframes: Dict[str, pd.DataFrame] = {}

    def run_sync(self) -> bool:
        """
        Run the full data synchronization process.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Mark job as started
            self.job.mark_started()
            self.job.total_endpoints = len(self.DASHBOARD_ENDPOINTS)
            self.db.commit()

            # Initialize PCO client
            self._init_client()

            # Test connection
            success, error = self.client.test_connection()
            if not success:
                raise Exception(f"PCO connection failed: {error}")

            # Fetch data from each endpoint
            total_records = 0
            for i, (name, config) in enumerate(self.DASHBOARD_ENDPOINTS.items()):
                self.job.update_progress(config['endpoint'], i)
                self.db.commit()

                records = self._fetch_endpoint(name, config)
                total_records += records

            # Explode check-ins by event_time_ids to match dbo.PC_CHECKINS format
            self._explode_checkins()

            # Enrich data with relationships
            self._enrich_event_times()
            self._enrich_checkins()

            # Load data to SQL Server
            self._load_to_database()

            # Update tenant and job
            self.tenant.last_data_refresh = datetime.now(timezone.utc)
            self.job.mark_completed(total_records)
            self.db.commit()

            logger.info(f"Sync completed for tenant {self.tenant.id}: {total_records} records")
            return True

        except Exception as e:
            logger.error(f"Sync failed for tenant {self.tenant.id}: {e}")
            self.job.mark_failed(str(e))
            self.db.commit()
            return False

    def _init_client(self):
        """Initialize PCO client with decrypted credentials."""
        if not self.tenant.has_credentials:
            raise Exception("PCO credentials not configured")

        app_id = decrypt_credential(self.tenant.pco_app_id_encrypted)
        secret = decrypt_credential(self.tenant.pco_secret_encrypted)
        self.client = PCOClient(app_id, secret)

    def _fetch_endpoint(self, name: str, config: Dict[str, Any]) -> int:
        """
        Fetch data from a single endpoint.

        Args:
            name: Endpoint name
            config: Endpoint configuration

        Returns:
            Number of records fetched
        """
        endpoint = config['endpoint']
        includes = config['includes']
        table_name = config['table_name']

        logger.info(f"Fetching {name} from {endpoint}")

        try:
            # Fetch all pages
            all_data = []
            offset = 0
            per_page = 100

            while True:
                params = {'per_page': per_page, 'offset': offset}
                response = self.client.get(endpoint, params=params, include=includes if includes else None)

                # Process response
                processed = process_jsonapi_response(response, endpoint)
                if not processed:
                    break

                all_data.extend(processed)

                # Check for more pages
                links = response.get('links', {})
                if 'next' not in links or not links['next']:
                    break

                offset += len(response.get('data', []))

            if all_data:
                # Convert to DataFrame
                df = pd.DataFrame(all_data)

                # Process DataFrame - use tenant's timezone
                df = convert_timestamps_to_timezone(df, table_name, self.tenant.data_timezone)
                df = add_derived_date_columns(df, table_name)
                df = prepare_dataframe_for_sql(df, table_name)

                # Add load timestamp
                df['load_timestamp'] = datetime.now(timezone.utc)

                self.dataframes[table_name] = df
                logger.info(f"Fetched {len(df)} records for {table_name}")
                return len(df)

            return 0

        except Exception as e:
            logger.error(f"Error fetching {name}: {e}")
            return 0

    def _explode_checkins(self):
        """
        Explode PC_CHECKINS by event_time_ids to create one row per event time.
        This matches the format of dbo.PC_CHECKINS loaded by planning_center_new.py.
        """
        if 'PC_CHECKINS' not in self.dataframes:
            logger.warning("PC_CHECKINS not found, skipping explosion")
            return

        df = self.dataframes['PC_CHECKINS']
        if df.empty:
            return

        # Find the event_time_ids column (may have different naming)
        event_time_ids_col = None
        for col_name in ['event_time_ids', 'EventTime_ids', 'event_times_ids']:
            if col_name in df.columns:
                event_time_ids_col = col_name
                break

        if event_time_ids_col is None:
            logger.warning("event_time_ids column not found in PC_CHECKINS, skipping explosion")
            return

        original_count = len(df)
        logger.info(f"Exploding PC_CHECKINS by {event_time_ids_col} (original: {original_count} rows)")

        # Parse event_time_ids column
        df[event_time_ids_col] = df[event_time_ids_col].apply(parse_event_time_ids)

        # Explode the DataFrame
        df_exploded = df.explode(event_time_ids_col)

        # Remove rows where event_time_ids is None/NaN after explode
        df_exploded = df_exploded[df_exploded[event_time_ids_col].notna()]

        # Also remove rows where it's an empty string after explode
        df_exploded = df_exploded[df_exploded[event_time_ids_col] != '']

        exploded_count = len(df_exploded)
        logger.info(f"Exploded PC_CHECKINS: {original_count} -> {exploded_count} rows")

        # Update the dataframe
        self.dataframes['PC_CHECKINS'] = df_exploded

    def _enrich_event_times(self):
        """
        Enrich PC_EVENT_TIMES with event name and frequency from PC_EVENTS.
        This matches the pattern in planning_center.py.
        """
        if 'PC_EVENT_TIMES' not in self.dataframes or 'PC_EVENTS' not in self.dataframes:
            logger.warning("Missing PC_EVENT_TIMES or PC_EVENTS, skipping event times enrichment")
            return

        event_times_df = self.dataframes['PC_EVENT_TIMES']
        events_df = self.dataframes['PC_EVENTS']

        if event_times_df.empty or events_df.empty:
            return

        # Find the event_id column in event_times
        event_id_col = None
        for col_name in ['event_id', 'events_id', 'event_ids']:
            if col_name in event_times_df.columns:
                event_id_col = col_name
                break

        if event_id_col is None:
            logger.warning("Could not find event_id column in PC_EVENT_TIMES")
            return

        # Find the id column in events
        events_id_col = None
        for col_name in ['event_id', 'events_id', 'id']:
            if col_name in events_df.columns:
                events_id_col = col_name
                break

        if events_id_col is None:
            logger.warning("Could not find id column in PC_EVENTS")
            return

        # Prepare events data for merge
        events_merge_cols = [events_id_col]
        rename_map = {}

        if 'name' in events_df.columns and 'event_name' not in event_times_df.columns:
            events_merge_cols.append('name')
            rename_map['name'] = 'event_name'

        if 'frequency' in events_df.columns and 'event_frequency' not in event_times_df.columns:
            events_merge_cols.append('frequency')
            rename_map['frequency'] = 'event_frequency'

        if len(events_merge_cols) == 1:
            logger.info("No new columns to add to PC_EVENT_TIMES from PC_EVENTS")
            return

        events_subset = events_df[events_merge_cols].copy()
        events_subset = events_subset.rename(columns=rename_map)
        events_subset = events_subset.rename(columns={events_id_col: event_id_col})

        # Merge
        original_cols = len(event_times_df.columns)
        event_times_df = event_times_df.merge(events_subset, on=event_id_col, how='left')

        new_cols = len(event_times_df.columns) - original_cols
        logger.info(f"Enriched PC_EVENT_TIMES with {new_cols} columns from PC_EVENTS")

        self.dataframes['PC_EVENT_TIMES'] = event_times_df

    def _enrich_checkins(self):
        """
        Enrich PC_CHECKINS with:
        1. Event times data (starts_at, event name)
        2. People demographics (gender, birthdate)
        This matches the pattern in planning_center.py.
        """
        if 'PC_CHECKINS' not in self.dataframes:
            logger.warning("PC_CHECKINS not found, skipping enrichment")
            return

        checkins_df = self.dataframes['PC_CHECKINS']
        if checkins_df.empty:
            return

        # Find the event_time_ids column in check-ins (after explosion, this contains single values)
        event_time_col = None
        for col_name in ['event_time_ids', 'EventTime_ids', 'event_times_ids']:
            if col_name in checkins_df.columns:
                event_time_col = col_name
                break

        # Enrich with event times data
        if event_time_col and 'PC_EVENT_TIMES' in self.dataframes:
            event_times_df = self.dataframes['PC_EVENT_TIMES']
            if not event_times_df.empty:
                # Find id column in event_times
                et_id_col = None
                for col_name in ['event_time_id', 'event_times_id', 'id']:
                    if col_name in event_times_df.columns:
                        et_id_col = col_name
                        break

                if et_id_col:
                    # Prepare event times subset for merge
                    et_merge_cols = [et_id_col]
                    rename_map = {}

                    if 'starts_at' in event_times_df.columns and 'event_starts_at' not in checkins_df.columns:
                        et_merge_cols.append('starts_at')
                        rename_map['starts_at'] = 'event_starts_at'

                    if 'event_name' in event_times_df.columns and 'event_name' not in checkins_df.columns:
                        et_merge_cols.append('event_name')

                    if 'event_frequency' in event_times_df.columns and 'event_frequency' not in checkins_df.columns:
                        et_merge_cols.append('event_frequency')

                    if len(et_merge_cols) > 1:
                        et_subset = event_times_df[et_merge_cols].copy()
                        et_subset = et_subset.rename(columns=rename_map)

                        # Convert both sides to same type for merge
                        checkins_df[event_time_col] = checkins_df[event_time_col].astype(str)
                        et_subset[et_id_col] = et_subset[et_id_col].astype(str)

                        original_cols = len(checkins_df.columns)
                        checkins_df = checkins_df.merge(
                            et_subset,
                            left_on=event_time_col,
                            right_on=et_id_col,
                            how='left'
                        )

                        # Drop the duplicate id column from merge if different name
                        if et_id_col != event_time_col and et_id_col in checkins_df.columns:
                            checkins_df = checkins_df.drop(columns=[et_id_col])

                        new_cols = len(checkins_df.columns) - original_cols
                        logger.info(f"Enriched PC_CHECKINS with {new_cols} columns from PC_EVENT_TIMES")

        # Enrich with people data (gender, birthdate)
        person_id_col = None
        for col_name in ['person_id', 'people_id', 'persons_id']:
            if col_name in checkins_df.columns:
                person_id_col = col_name
                break

        if person_id_col and 'PC_PEOPLE' in self.dataframes:
            people_df = self.dataframes['PC_PEOPLE']
            if not people_df.empty:
                # Find id column in people
                people_id_col = None
                for col_name in ['people_id', 'person_id', 'id']:
                    if col_name in people_df.columns:
                        people_id_col = col_name
                        break

                if people_id_col:
                    # Prepare people subset for merge
                    people_merge_cols = [people_id_col]
                    rename_map = {}

                    if 'gender' in people_df.columns and 'person_gender' not in checkins_df.columns:
                        people_merge_cols.append('gender')
                        rename_map['gender'] = 'person_gender'

                    if 'birthdate' in people_df.columns and 'person_birthdate' not in checkins_df.columns:
                        people_merge_cols.append('birthdate')
                        rename_map['birthdate'] = 'person_birthdate'

                    if len(people_merge_cols) > 1:
                        people_subset = people_df[people_merge_cols].copy()
                        people_subset = people_subset.rename(columns=rename_map)

                        # Convert both sides to same type for merge
                        checkins_df[person_id_col] = checkins_df[person_id_col].astype(str)
                        people_subset[people_id_col] = people_subset[people_id_col].astype(str)

                        original_cols = len(checkins_df.columns)
                        checkins_df = checkins_df.merge(
                            people_subset,
                            left_on=person_id_col,
                            right_on=people_id_col,
                            how='left'
                        )

                        # Drop the duplicate id column from merge if different name
                        if people_id_col != person_id_col and people_id_col in checkins_df.columns:
                            checkins_df = checkins_df.drop(columns=[people_id_col])

                        new_cols = len(checkins_df.columns) - original_cols
                        logger.info(f"Enriched PC_CHECKINS with {new_cols} columns from PC_PEOPLE")

        self.dataframes['PC_CHECKINS'] = checkins_df

    def _ensure_schema_exists(self):
        """Create the SQL schema if it doesn't exist."""
        schema = self.schema_name
        logger.info(f"Ensuring schema [{schema}] exists")

        with engine.begin() as conn:
            # Check if schema exists
            result = conn.execute(text(
                "SELECT 1 FROM sys.schemas WHERE name = :schema"
            ), {"schema": schema})

            if not result.fetchone():
                # Create the schema
                conn.execute(text(f"CREATE SCHEMA [{schema}]"))
                logger.info(f"Created schema [{schema}]")
            else:
                logger.info(f"Schema [{schema}] already exists")

    def _load_to_database(self):
        """Load all DataFrames to SQL Server using tenant schema."""
        # First ensure the schema exists
        self._ensure_schema_exists()

        for table_name, df in self.dataframes.items():
            if df.empty:
                continue

            # Full table name with schema: schema.table_name
            full_table_name = f"{self.schema_name}.{table_name}"
            logger.info(f"Loading {len(df)} records to [{full_table_name}]")

            try:
                # Drop existing table if it exists
                with engine.begin() as conn:
                    conn.execute(text(f"DROP TABLE IF EXISTS [{self.schema_name}].[{table_name}]"))

                # Generate dtype mapping
                dtype_mapping = generate_dtype_mapping(df)

                # Load data using schema parameter
                df.to_sql(
                    table_name,
                    con=engine,
                    schema=self.schema_name,
                    if_exists='replace',
                    index=False,
                    dtype=dtype_mapping
                )

                logger.info(f"Successfully loaded [{full_table_name}]")

            except Exception as e:
                logger.error(f"Error loading [{full_table_name}]: {e}")
                raise


def run_data_refresh(job_id: str, tenant_id: str):
    """
    Background task to run data refresh.

    Args:
        job_id: UUID of the DataRefreshJob
        tenant_id: UUID of the Tenant
    """
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        job = db.query(DataRefreshJob).filter(DataRefreshJob.id == job_id).first()

        if not tenant or not job:
            logger.error(f"Tenant or job not found: tenant={tenant_id}, job={job_id}")
            return

        service = DataSyncService(tenant, job, db)
        service.run_sync()

    except Exception as e:
        logger.error(f"Background refresh failed: {e}")
    finally:
        db.close()
