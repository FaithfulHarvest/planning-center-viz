"""
Chart data service for generating visualization data from tenant tables.
"""
import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import engine
from app.models import Tenant

logger = logging.getLogger(__name__)


class ChartService:
    """Service for generating chart data from tenant tables."""

    def __init__(self, tenant: Tenant):
        """
        Initialize chart service.

        Args:
            tenant: Tenant to get chart data for
        """
        self.tenant = tenant
        self.schema_name = tenant.schema_name  # SQL schema name (e.g., gf_paradise_tx)

    def get_attendance_over_time(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        granularity: str = 'week'
    ) -> List[Dict[str, Any]]:
        """
        Get attendance data over time.

        Args:
            start_date: Start date (default: 3 months ago)
            end_date: End date (default: today)
            granularity: 'day', 'week', or 'month'

        Returns:
            List of data points with period, total_checkins, unique_people
        """
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=90)

        # Date truncation based on granularity
        if granularity == 'day':
            date_trunc = "CAST(created_at AS DATE)"
        elif granularity == 'month':
            date_trunc = "DATEFROMPARTS(YEAR(created_at), MONTH(created_at), 1)"
        else:  # week
            date_trunc = "DATEADD(WEEK, DATEDIFF(WEEK, 0, created_at), 0)"

        query = f"""
            SELECT
                {date_trunc} AS period,
                COUNT(*) AS total_checkins,
                COUNT(DISTINCT person_id) AS unique_people
            FROM [{self.schema_name}].[PC_CHECKINS]
            WHERE created_at >= :start_date
              AND created_at <= :end_date
            GROUP BY {date_trunc}
            ORDER BY period
        """

        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text(query),
                    {"start_date": start_date, "end_date": end_date}
                )
                return [
                    {
                        "period": row.period.isoformat() if row.period else None,
                        "total_checkins": row.total_checkins,
                        "unique_people": row.unique_people
                    }
                    for row in result
                ]
        except Exception as e:
            logger.error(f"Error getting attendance data: {e}")
            return []

    def get_event_breakdown(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get check-ins broken down by event.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List of events with name, count, percentage
        """
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=90)

        query = f"""
            WITH event_counts AS (
                SELECT
                    COALESCE(event_name, 'Unknown') AS event_name,
                    COUNT(*) AS count
                FROM [{self.schema_name}].[PC_CHECKINS]
                WHERE created_at >= :start_date
                  AND created_at <= :end_date
                GROUP BY event_name
            ),
            total AS (
                SELECT SUM(count) AS total_count FROM event_counts
            )
            SELECT
                ec.event_name,
                ec.count,
                CAST(ec.count AS FLOAT) / NULLIF(t.total_count, 0) * 100 AS percentage
            FROM event_counts ec
            CROSS JOIN total t
            ORDER BY ec.count DESC
        """

        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text(query),
                    {"start_date": start_date, "end_date": end_date}
                )
                return [
                    {
                        "event_name": row.event_name or "Unknown",
                        "count": row.count,
                        "percentage": round(row.percentage or 0, 1)
                    }
                    for row in result
                ]
        except Exception as e:
            logger.error(f"Error getting event breakdown: {e}")
            return []

    def get_demographics(self) -> Dict[str, Any]:
        """
        Get demographic data (age groups, gender distribution).

        Returns:
            Dictionary with age_groups, gender_distribution, total_people
        """
        # Gender distribution
        gender_query = f"""
            SELECT
                COALESCE(gender, 'Unknown') AS gender,
                COUNT(*) AS count
            FROM [{self.schema_name}].[PC_PEOPLE]
            GROUP BY gender
        """

        # Age groups (from birthdate)
        age_query = f"""
            WITH ages AS (
                SELECT
                    CASE
                        WHEN birthdate IS NULL THEN 'Unknown'
                        WHEN DATEDIFF(YEAR, birthdate, GETDATE()) < 13 THEN 'Children (0-12)'
                        WHEN DATEDIFF(YEAR, birthdate, GETDATE()) < 18 THEN 'Teens (13-17)'
                        WHEN DATEDIFF(YEAR, birthdate, GETDATE()) < 30 THEN 'Young Adults (18-29)'
                        WHEN DATEDIFF(YEAR, birthdate, GETDATE()) < 45 THEN 'Adults (30-44)'
                        WHEN DATEDIFF(YEAR, birthdate, GETDATE()) < 60 THEN 'Middle Age (45-59)'
                        ELSE 'Seniors (60+)'
                    END AS age_group
                FROM [{self.schema_name}].[PC_PEOPLE]
            )
            SELECT age_group, COUNT(*) AS count
            FROM ages
            GROUP BY age_group
            ORDER BY
                CASE age_group
                    WHEN 'Children (0-12)' THEN 1
                    WHEN 'Teens (13-17)' THEN 2
                    WHEN 'Young Adults (18-29)' THEN 3
                    WHEN 'Adults (30-44)' THEN 4
                    WHEN 'Middle Age (45-59)' THEN 5
                    WHEN 'Seniors (60+)' THEN 6
                    ELSE 7
                END
        """

        total_query = f"SELECT COUNT(*) AS total FROM [{self.schema_name}].[PC_PEOPLE]"

        try:
            with engine.connect() as conn:
                # Get gender distribution
                gender_result = conn.execute(text(gender_query))
                gender_data = list(gender_result)
                gender_total = sum(row.count for row in gender_data)

                gender_distribution = [
                    {
                        "gender": row.gender,
                        "count": row.count,
                        "percentage": round(row.count / gender_total * 100, 1) if gender_total > 0 else 0
                    }
                    for row in gender_data
                ]

                # Get age groups
                age_result = conn.execute(text(age_query))
                age_data = list(age_result)
                age_total = sum(row.count for row in age_data)

                age_groups = [
                    {
                        "age_group": row.age_group,
                        "count": row.count,
                        "percentage": round(row.count / age_total * 100, 1) if age_total > 0 else 0
                    }
                    for row in age_data
                ]

                # Get total
                total_result = conn.execute(text(total_query))
                total_people = total_result.scalar() or 0

                return {
                    "gender_distribution": gender_distribution,
                    "age_groups": age_groups,
                    "total_people": total_people
                }

        except Exception as e:
            logger.error(f"Error getting demographics: {e}")
            return {
                "gender_distribution": [],
                "age_groups": [],
                "total_people": 0
            }

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics for the dashboard.

        Returns:
            Dictionary with total_people, total_checkins, etc.
        """
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        last_week_start = week_start - timedelta(days=7)
        last_week_end = week_start - timedelta(days=1)

        try:
            with engine.connect() as conn:
                # Total people
                total_people = conn.execute(
                    text(f"SELECT COUNT(*) FROM [{self.schema_name}].[PC_PEOPLE]")
                ).scalar() or 0

                # Total check-ins
                total_checkins = conn.execute(
                    text(f"SELECT COUNT(*) FROM [{self.schema_name}].[PC_CHECKINS]")
                ).scalar() or 0

                # This week's check-ins
                checkins_this_week = conn.execute(
                    text(f"""
                        SELECT COUNT(*) FROM [{self.schema_name}].[PC_CHECKINS]
                        WHERE created_at >= :week_start
                    """),
                    {"week_start": week_start}
                ).scalar() or 0

                # Last week's check-ins
                checkins_last_week = conn.execute(
                    text(f"""
                        SELECT COUNT(*) FROM [{self.schema_name}].[PC_CHECKINS]
                        WHERE created_at >= :last_week_start
                          AND created_at <= :last_week_end
                    """),
                    {"last_week_start": last_week_start, "last_week_end": last_week_end}
                ).scalar() or 0

                # Week over week change
                if checkins_last_week > 0:
                    wow_change = ((checkins_this_week - checkins_last_week) / checkins_last_week) * 100
                else:
                    wow_change = 0.0

                # Most popular event
                popular_event_result = conn.execute(
                    text(f"""
                        SELECT TOP 1 event_name
                        FROM [{self.schema_name}].[PC_CHECKINS]
                        WHERE created_at >= :week_start
                        GROUP BY event_name
                        ORDER BY COUNT(*) DESC
                    """),
                    {"week_start": week_start}
                )
                popular_event = popular_event_result.scalar()

                return {
                    "total_people": total_people,
                    "total_checkins": total_checkins,
                    "checkins_this_week": checkins_this_week,
                    "checkins_last_week": checkins_last_week,
                    "week_over_week_change": round(wow_change, 1),
                    "most_popular_event": popular_event
                }

        except Exception as e:
            logger.error(f"Error getting summary stats: {e}")
            return {
                "total_people": 0,
                "total_checkins": 0,
                "checkins_this_week": 0,
                "checkins_last_week": 0,
                "week_over_week_change": 0.0,
                "most_popular_event": None
            }
