"""Chart data API endpoints."""
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.dependencies import verify_trial_active
from app.services.chart_service import ChartService
from app.schemas.charts import SummaryStats

router = APIRouter()


@router.get("/attendance")
async def get_attendance_data(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    granularity: str = Query("week", description="Granularity: day, week, or month"),
    current_user: User = Depends(verify_trial_active),
    db: Session = Depends(get_db)
):
    """
    Get attendance over time data for chart.
    """
    chart_service = ChartService(current_user.tenant)
    data = chart_service.get_attendance_over_time(start_date, end_date, granularity)

    return {
        "data": data,
        "metadata": {
            "start_date": str(start_date) if start_date else None,
            "end_date": str(end_date) if end_date else None,
            "granularity": granularity
        }
    }


@router.get("/events")
async def get_event_breakdown(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(verify_trial_active),
    db: Session = Depends(get_db)
):
    """
    Get event breakdown data for chart.
    """
    chart_service = ChartService(current_user.tenant)
    data = chart_service.get_event_breakdown(start_date, end_date)

    return {
        "data": data,
        "metadata": {
            "start_date": str(start_date) if start_date else None,
            "end_date": str(end_date) if end_date else None
        }
    }


@router.get("/demographics")
async def get_demographics_data(
    current_user: User = Depends(verify_trial_active),
    db: Session = Depends(get_db)
):
    """
    Get demographics data for charts (age groups, gender distribution).
    """
    chart_service = ChartService(current_user.tenant)
    data = chart_service.get_demographics()

    return data


@router.get("/summary", response_model=SummaryStats)
async def get_summary_stats(
    current_user: User = Depends(verify_trial_active),
    db: Session = Depends(get_db)
):
    """
    Get summary statistics for the dashboard.
    """
    chart_service = ChartService(current_user.tenant)
    data = chart_service.get_summary_stats()

    return SummaryStats(**data)
