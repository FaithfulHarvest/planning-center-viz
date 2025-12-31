"""Data viewer API endpoints."""
import json
from typing import List, Optional, Dict, Any, Tuple, Set
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from app.database import get_db, engine
from app.models import User, Tenant
from app.dependencies import get_current_user

router = APIRouter()


def build_filter_clauses(
    filter_dict: Dict[str, Any],
    valid_columns: Set[str],
    param_prefix: str = "filter"
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Build WHERE clause conditions from filter dictionary.

    Returns:
        Tuple of (list of WHERE clause strings, dict of parameters)
    """
    where_clauses = []
    params = {}

    for i, (col, value) in enumerate(filter_dict.items()):
        if col not in valid_columns:
            continue

        if isinstance(value, list) and len(value) > 0:
            # Multi-select: IN clause
            placeholders = []
            for j, v in enumerate(value):
                param_name = f"{param_prefix}_{i}_{j}"
                placeholders.append(f":{param_name}")
                params[param_name] = v
            where_clauses.append(f"CAST([{col}] AS NVARCHAR(MAX)) IN ({', '.join(placeholders)})")

        elif isinstance(value, dict):
            # Date range: BETWEEN clause
            if "from" in value and value["from"]:
                param_name = f"{param_prefix}_{i}_from"
                where_clauses.append(f"[{col}] >= :{param_name}")
                params[param_name] = value["from"]
            if "to" in value and value["to"]:
                param_name = f"{param_prefix}_{i}_to"
                where_clauses.append(f"[{col}] <= :{param_name}")
                params[param_name] = value["to"]

        elif isinstance(value, str) and value:
            # Simple string: LIKE search
            param_name = f"{param_prefix}_{i}"
            where_clauses.append(f"CAST([{col}] AS NVARCHAR(MAX)) LIKE :{param_name}")
            params[param_name] = f"%{value}%"

    return where_clauses, params


class TableInfo(BaseModel):
    name: str
    row_count: int


class ColumnInfo(BaseModel):
    name: str
    data_type: str
    is_nullable: bool


class TableDataResponse(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_count: int
    page: int
    per_page: int
    total_pages: int


class DistinctValuesResponse(BaseModel):
    column: str
    values: List[Any]
    total_count: int


@router.get("/tables", response_model=List[TableInfo])
def get_available_tables(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of available tables for the tenant's schema."""
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    schema_name = tenant.schema_name

    try:
        with engine.connect() as conn:
            # Get tables in the tenant's schema with row counts
            # Join with sys.schemas to ensure we only count rows for tables in the correct schema
            result = conn.execute(text("""
                SELECT
                    t.TABLE_NAME,
                    p.rows AS row_count
                FROM INFORMATION_SCHEMA.TABLES t
                LEFT JOIN sys.schemas s ON s.name = t.TABLE_SCHEMA
                LEFT JOIN sys.tables st ON st.name = t.TABLE_NAME AND st.schema_id = s.schema_id
                LEFT JOIN sys.partitions p ON st.object_id = p.object_id AND p.index_id IN (0, 1)
                WHERE t.TABLE_SCHEMA = :schema_name
                AND t.TABLE_TYPE = 'BASE TABLE'
                ORDER BY t.TABLE_NAME
            """), {"schema_name": schema_name})

            tables = []
            for row in result:
                tables.append(TableInfo(
                    name=row[0],
                    row_count=row[1] or 0
                ))

            return tables
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tables: {str(e)}")


@router.get("/tables/{table_name}/columns", response_model=List[ColumnInfo])
def get_table_columns(
    table_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get column information for a specific table."""
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    schema_name = tenant.schema_name

    try:
        with engine.connect() as conn:
            # Verify table exists in tenant's schema
            check_result = conn.execute(text("""
                SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = :schema_name AND TABLE_NAME = :table_name
            """), {"schema_name": schema_name, "table_name": table_name})

            if not check_result.fetchone():
                raise HTTPException(status_code=404, detail="Table not found")

            # Get column information
            result = conn.execute(text("""
                SELECT
                    COLUMN_NAME,
                    DATA_TYPE,
                    IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = :schema_name AND TABLE_NAME = :table_name
                ORDER BY ORDINAL_POSITION
            """), {"schema_name": schema_name, "table_name": table_name})

            columns = []
            for row in result:
                columns.append(ColumnInfo(
                    name=row[0],
                    data_type=row[1],
                    is_nullable=row[2] == "YES"
                ))

            return columns
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching columns: {str(e)}")


@router.get("/tables/{table_name}/columns/{column_name}/distinct", response_model=DistinctValuesResponse)
def get_distinct_values(
    table_name: str,
    column_name: str,
    search: Optional[str] = Query(None, description="Search filter for values"),
    filters: Optional[str] = Query(None, description="JSON string of existing filters to apply"),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get distinct values for a column (for filter dropdowns), respecting existing filters."""
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    schema_name = tenant.schema_name

    try:
        with engine.connect() as conn:
            # Get all valid columns for this table
            valid_cols_result = conn.execute(text("""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = :schema_name AND TABLE_NAME = :table_name
            """), {"schema_name": schema_name, "table_name": table_name})
            valid_columns = {row[0] for row in valid_cols_result}

            if column_name not in valid_columns:
                raise HTTPException(status_code=404, detail="Column not found")

            # Build WHERE clauses
            where_clauses = []
            params = {}

            # Add search filter for the current column
            if search:
                where_clauses.append(f"CAST([{column_name}] AS NVARCHAR(MAX)) LIKE :search")
                params["search"] = f"%{search}%"

            # Apply existing filters (excluding the current column being filtered)
            if filters:
                try:
                    filter_dict = json.loads(filters)
                    # Remove the current column from filters so we don't filter it against itself
                    filter_dict_without_current = {k: v for k, v in filter_dict.items() if k != column_name}
                    if filter_dict_without_current:
                        filter_clauses, filter_params = build_filter_clauses(
                            filter_dict_without_current, valid_columns
                        )
                        where_clauses.extend(filter_clauses)
                        params.update(filter_params)
                except json.JSONDecodeError:
                    pass

            where_sql = ""
            if where_clauses:
                where_sql = "WHERE " + " AND ".join(where_clauses)

            # Get distinct values
            query = f"""
                SELECT DISTINCT TOP {limit} [{column_name}]
                FROM [{schema_name}].[{table_name}]
                {where_sql}
                ORDER BY [{column_name}]
            """

            result = conn.execute(text(query), params)
            values = []
            for row in result:
                val = row[0]
                if val is not None:
                    if not isinstance(val, (str, int, float, bool)):
                        val = str(val)
                    values.append(val)

            # Get total distinct count (with filters applied)
            count_query = f"""
                SELECT COUNT(DISTINCT [{column_name}])
                FROM [{schema_name}].[{table_name}]
                {where_sql}
            """
            total_count = conn.execute(text(count_query), params).scalar() or 0

            return DistinctValuesResponse(
                column=column_name,
                values=values,
                total_count=total_count
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching distinct values: {str(e)}")


@router.get("/tables/{table_name}/data", response_model=TableDataResponse)
def get_table_data(
    table_name: str,
    columns: Optional[str] = Query(None, description="Comma-separated list of columns to include"),
    filters: Optional[str] = Query(None, description="JSON string of column:value filters"),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get paginated data from a table with optional column selection and filters."""
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    schema_name = tenant.schema_name

    try:
        with engine.connect() as conn:
            # Verify table exists
            check_result = conn.execute(text("""
                SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = :schema_name AND TABLE_NAME = :table_name
            """), {"schema_name": schema_name, "table_name": table_name})

            if not check_result.fetchone():
                raise HTTPException(status_code=404, detail="Table not found")

            # Get valid columns for this table
            valid_cols_result = conn.execute(text("""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = :schema_name AND TABLE_NAME = :table_name
            """), {"schema_name": schema_name, "table_name": table_name})
            valid_columns = {row[0] for row in valid_cols_result}

            # Determine which columns to select
            if columns:
                selected_columns = [c.strip() for c in columns.split(",") if c.strip() in valid_columns]
                if not selected_columns:
                    selected_columns = list(valid_columns)
            else:
                selected_columns = list(valid_columns)

            # Build column list for SQL (with proper escaping)
            column_list = ", ".join([f"[{col}]" for col in selected_columns])

            # Build WHERE clause from filters using helper function
            where_clauses = []
            params = {}

            if filters:
                try:
                    filter_dict = json.loads(filters)
                    where_clauses, params = build_filter_clauses(filter_dict, valid_columns)
                except json.JSONDecodeError:
                    pass

            where_sql = ""
            if where_clauses:
                where_sql = "WHERE " + " AND ".join(where_clauses)

            # Get total count
            count_sql = f"SELECT COUNT(*) FROM [{schema_name}].[{table_name}] {where_sql}"
            total_count = conn.execute(text(count_sql), params).scalar()

            # Calculate pagination
            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
            offset = (page - 1) * per_page

            # Get paginated data
            data_sql = f"""
                SELECT {column_list}
                FROM [{schema_name}].[{table_name}]
                {where_sql}
                ORDER BY (SELECT NULL)
                OFFSET :offset ROWS
                FETCH NEXT :per_page ROWS ONLY
            """

            params["offset"] = offset
            params["per_page"] = per_page

            result = conn.execute(text(data_sql), params)

            rows = []
            for row in result:
                row_dict = {}
                for i, col in enumerate(selected_columns):
                    value = row[i]
                    # Convert non-serializable types to strings
                    if value is not None and not isinstance(value, (str, int, float, bool)):
                        value = str(value)
                    row_dict[col] = value
                rows.append(row_dict)

            return TableDataResponse(
                columns=selected_columns,
                rows=rows,
                total_count=total_count,
                page=page,
                per_page=per_page,
                total_pages=total_pages
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")
