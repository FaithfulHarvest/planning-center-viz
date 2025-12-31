"""
Data processing utilities extracted from planning_center_new.py.
Handles JSON:API response processing, timestamp conversion, and SQL compatibility.
"""
import json
import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict
import pandas as pd
import pytz

logger = logging.getLogger(__name__)


def convert_complex_type_to_json(value: Any) -> Any:
    """
    Convert complex Python types (lists, dicts) to JSON strings for SQL Server compatibility.

    Args:
        value: Value to convert

    Returns:
        JSON string if complex type, original value otherwise
    """
    if isinstance(value, (list, dict)):
        try:
            return json.dumps(value)
        except (TypeError, ValueError) as e:
            logger.warning(f"Could not convert complex type to JSON: {e}")
            return None
    return value


def process_jsonapi_response(response: Dict[str, Any], endpoint: str) -> List[Dict[str, Any]]:
    """
    Process a JSON:API response into a flat list of dictionaries.
    Detects and converts complex types (lists, dicts) to JSON strings for SQL Server compatibility.

    Args:
        response: JSON:API response dictionary
        endpoint: The endpoint that was called

    Returns:
        List of flattened dictionaries with SQL-compatible types
    """
    detected_types = defaultdict(set)

    try:
        data_items = response.get('data', [])
        included_items = response.get('included', [])

        # Create lookup for included items
        included_lookup = {}
        for item in included_items:
            item_id = item.get('id')
            item_type = item.get('type', '')
            if item_id and item_type:
                included_lookup[f"{item_id}_{item_type}"] = item

        processed_data = []

        for item in data_items:
            # Start with ID and attributes
            item_id = item.get('id')
            item_type = item.get('type', '')
            attributes = item.get('attributes', {})
            relationships = item.get('relationships', {})

            # Create base dictionary and convert complex types
            data_dict = {f'{item_type}_id': item_id}
            for attr_name, attr_value in attributes.items():
                # Convert complex types to JSON strings
                if isinstance(attr_value, (list, dict)):
                    detected_types[attr_name].add(type(attr_value).__name__)
                    data_dict[attr_name] = convert_complex_type_to_json(attr_value)
                else:
                    data_dict[attr_name] = attr_value

            # Process relationships
            for rel_name, rel_data in relationships.items():
                if not rel_data or 'data' not in rel_data:
                    continue

                rel_items = rel_data['data']
                if not isinstance(rel_items, list):
                    rel_items = [rel_items] if rel_items else []

                # Store relationship IDs
                rel_ids = []
                for rel_item in rel_items:
                    if isinstance(rel_item, dict):
                        rel_id = rel_item.get('id')
                        rel_type = rel_item.get('type', '')
                        if rel_id:
                            rel_ids.append(rel_id)

                            # Try to get included data
                            lookup_key = f"{rel_id}_{rel_type}"
                            included_data = included_lookup.get(lookup_key)

                            if included_data:
                                included_attrs = included_data.get('attributes', {})
                                # Add included attributes with prefix
                                for attr_name, attr_value in included_attrs.items():
                                    col_name = f'{rel_type}_{attr_name}'
                                    if isinstance(attr_value, (list, dict)):
                                        detected_types[col_name].add(type(attr_value).__name__)
                                        data_dict[col_name] = convert_complex_type_to_json(attr_value)
                                    else:
                                        data_dict[col_name] = attr_value

                # Store relationship IDs
                if rel_ids:
                    if len(rel_ids) == 1:
                        data_dict[f'{rel_name}_id'] = rel_ids[0]
                    detected_types[f'{rel_name}_ids'].add('list')
                    data_dict[f'{rel_name}_ids'] = convert_complex_type_to_json(rel_ids)

            processed_data.append(data_dict)

        return processed_data

    except Exception as e:
        logger.error(f"Error processing response from {endpoint}: {e}")
        return []


def convert_timestamps_to_timezone(df: pd.DataFrame, df_name: str, target_timezone: str = 'US/Central') -> pd.DataFrame:
    """
    Detect and convert timestamp columns to the specified timezone by examining actual data.

    Args:
        df: DataFrame to process
        df_name: Name of the DataFrame (for logging)
        target_timezone: Target timezone string (e.g., 'US/Central', 'US/Eastern')

    Returns:
        DataFrame with timestamps converted to target timezone
    """
    df = df.copy()
    target_tz = pytz.timezone(target_timezone)
    converted_columns = []

    for col in df.columns:
        if df[col].isna().all():
            continue

        if pd.api.types.is_datetime64_any_dtype(df[col]):
            try:
                if df[col].dt.tz is not None:
                    df[col] = df[col].dt.tz_convert(target_tz)
                    converted_columns.append(col)
                else:
                    df[col] = df[col].dt.tz_localize('UTC').dt.tz_convert(target_tz)
                    converted_columns.append(col)
            except Exception as e:
                logger.debug(f"Could not convert {col} in {df_name}: {e}")
                continue
        elif df[col].dtype == 'object':
            sample = df[col].dropna().head(50)

            if len(sample) == 0:
                continue

            try:
                sample_strs = [str(val) for val in sample.head(10)]
                looks_like_timestamp = any(
                    'T' in s or (':' in s and len(s) > 15) or s.endswith('Z') or
                    ('-' in s and len(s.split('-')) >= 3 and ':' in s)
                    for s in sample_strs
                )

                if not looks_like_timestamp:
                    continue

                parsed = pd.to_datetime(sample, errors='coerce', utc=True)
                success_rate = parsed.notna().sum() / len(sample) if len(sample) > 0 else 0

                if success_rate >= 0.7:
                    has_time_info = any(
                        'T' in str(val) or ':' in str(val) or str(val).endswith('Z') or
                        (isinstance(val, str) and (len(val) > 15 or ('-' in val and val.count(':') >= 2)))
                        for val in sample.head(10)
                    )

                    if has_time_info:
                        parsed_full = pd.to_datetime(df[col], errors='coerce', utc=True)
                        if parsed_full.notna().sum() > 0:
                            df[col] = parsed_full.dt.tz_convert(target_tz)
                            converted_columns.append(col)
            except Exception as e:
                logger.debug(f"Could not parse timestamps in {col} in {df_name}: {e}")
                continue

    if converted_columns:
        logger.info(f"Converted {len(converted_columns)} timestamp columns to {target_timezone} in {df_name}")

    return df


# Backwards compatibility alias
def convert_timestamps_to_central_time(df: pd.DataFrame, df_name: str) -> pd.DataFrame:
    """Backwards compatible alias for convert_timestamps_to_timezone with US/Central default."""
    return convert_timestamps_to_timezone(df, df_name, 'US/Central')


def add_derived_date_columns(df: pd.DataFrame, df_name: str) -> pd.DataFrame:
    """
    Add derived date and time columns from datetime columns.
    For each datetime column ending in '_at', creates '_date' and '_time' columns.

    Args:
        df: DataFrame to process
        df_name: Name of the DataFrame (for logging)

    Returns:
        DataFrame with added derived columns
    """
    df = df.copy()
    added_columns = []

    for col in list(df.columns):
        # Only process columns that end with '_at' and are datetime
        if not col.endswith('_at'):
            continue

        # Check if it's a datetime column
        if not pd.api.types.is_datetime64_any_dtype(df[col]):
            continue

        # Create base name (e.g., 'created_at' -> 'created')
        base_name = col[:-3]  # Remove '_at'

        # Add date column
        date_col = f"{base_name}_date"
        if date_col not in df.columns:
            try:
                df[date_col] = df[col].dt.date
                added_columns.append(date_col)
            except Exception as e:
                logger.debug(f"Could not create {date_col} in {df_name}: {e}")

        # Add time column
        time_col = f"{base_name}_time"
        if time_col not in df.columns:
            try:
                df[time_col] = df[col].dt.strftime('%H:%M:%S')
                added_columns.append(time_col)
            except Exception as e:
                logger.debug(f"Could not create {time_col} in {df_name}: {e}")

    if added_columns:
        logger.info(f"Added {len(added_columns)} derived date/time columns in {df_name}: {added_columns}")

    return df


def prepare_dataframe_for_sql(df: pd.DataFrame, df_name: str) -> pd.DataFrame:
    """
    Prepare DataFrame for SQL Server by converting complex types to JSON strings.

    Args:
        df: DataFrame to prepare
        df_name: Name of the DataFrame (for logging)

    Returns:
        Prepared DataFrame with SQL-compatible types
    """
    df = df.copy()
    converted_columns = []

    for col in df.columns:
        sample_values = df[col].dropna().head(100)

        if len(sample_values) == 0:
            continue

        needs_conversion = False
        complex_type = None

        for val in sample_values:
            if isinstance(val, str):
                val_stripped = val.strip()
                if (val_stripped.startswith('[') and val_stripped.endswith(']')) or \
                   (val_stripped.startswith('{') and val_stripped.endswith('}')):
                    try:
                        json.loads(val_stripped)
                        continue
                    except (json.JSONDecodeError, ValueError):
                        try:
                            import ast
                            parsed = ast.literal_eval(val_stripped)
                            if isinstance(parsed, (list, dict)):
                                needs_conversion = True
                                complex_type = type(parsed).__name__
                                break
                        except:
                            pass
            elif isinstance(val, (list, dict)):
                needs_conversion = True
                complex_type = type(val).__name__
                break

        if needs_conversion:
            def convert_value(v):
                if pd.isna(v):
                    return None
                if isinstance(v, (list, dict)):
                    return convert_complex_type_to_json(v)
                if isinstance(v, str):
                    try:
                        import ast
                        parsed = ast.literal_eval(v)
                        if isinstance(parsed, (list, dict)):
                            return convert_complex_type_to_json(parsed)
                    except:
                        pass
                return v

            try:
                df[col] = df[col].apply(convert_value)
                converted_columns.append((col, complex_type))
            except Exception as e:
                logger.warning(f"Could not convert column '{col}' in {df_name}: {e}")

    if converted_columns:
        logger.info(f"Converted {len(converted_columns)} columns to JSON strings in {df_name}")

    return df


def generate_dtype_mapping(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate SQLAlchemy dtype mapping for a DataFrame based on column types and names.

    Args:
        df: DataFrame to generate mapping for

    Returns:
        Dictionary mapping column names to SQLAlchemy types
    """
    from sqlalchemy import Boolean, Text, Integer, Date, String, Float, DateTime

    dtype_mapping = {}

    for col in df.columns:
        col_lower = col.lower()

        # ID columns
        if col.endswith('_id') or col.endswith('_ids'):
            dtype_mapping[col] = Integer if not col.endswith('_ids') else Text

        # Boolean columns
        elif any(x in col_lower for x in ['is_', 'has_', 'can_', 'primary', 'blocked', 'verified', 'opened']):
            if df[col].dtype != 'object':
                dtype_mapping[col] = Boolean
            else:
                sample = df[col].dropna().head(20)
                if len(sample) > 0:
                    unique_vals = set(str(v).lower().strip() for v in sample.unique())
                    bool_like = unique_vals.issubset({'true', 'false', '1', '0', 'yes', 'no', 't', 'f', 'y', 'n', ''})
                    if bool_like and len(unique_vals) <= 3:
                        dtype_mapping[col] = Boolean
                    else:
                        max_len = sample.astype(str).str.len().max() if len(sample) > 0 else 0
                        dtype_mapping[col] = Text if max_len > 255 else String(255)
                else:
                    dtype_mapping[col] = Boolean

        # Date columns
        elif 'date' in col_lower or col.endswith('_at'):
            if 'date' in col_lower and 'time' not in col_lower:
                dtype_mapping[col] = Date
            else:
                dtype_mapping[col] = DateTime(timezone=True)

        # Numeric columns
        elif any(x in col_lower for x in ['count', 'total', 'min', 'max', 'grade', 'year']):
            if df[col].dtype in ['int64', 'Int64']:
                dtype_mapping[col] = Integer
            elif df[col].dtype in ['float64', 'Float64']:
                dtype_mapping[col] = Float
            else:
                dtype_mapping[col] = String(255)

        # Text/JSON columns
        elif df[col].dtype == 'object':
            sample = df[col].dropna().head(10)
            if len(sample) > 0:
                first_val = str(sample.iloc[0])
                if first_val.startswith('[') or first_val.startswith('{'):
                    dtype_mapping[col] = Text
                elif 'notes' in col_lower or 'description' in col_lower or len(first_val) > 255:
                    dtype_mapping[col] = Text
                else:
                    dtype_mapping[col] = String(255)
            else:
                dtype_mapping[col] = String(255)

        # Default based on pandas dtype
        elif df[col].dtype == 'bool':
            dtype_mapping[col] = Boolean
        elif df[col].dtype in ['int64', 'Int64']:
            dtype_mapping[col] = Integer
        elif df[col].dtype in ['float64', 'Float64']:
            dtype_mapping[col] = Float
        else:
            dtype_mapping[col] = String(255)

    return dtype_mapping
