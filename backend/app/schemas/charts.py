"""Chart data schemas."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class AttendanceDataPoint(BaseModel):
    """Single data point for attendance chart."""
    period: str  # Date string
    total_checkins: int
    unique_people: int


class EventBreakdown(BaseModel):
    """Event breakdown data."""
    event_name: str
    count: int
    percentage: float


class AgeGroup(BaseModel):
    """Age group distribution."""
    age_group: str
    count: int
    percentage: float


class GenderDistribution(BaseModel):
    """Gender distribution."""
    gender: str
    count: int
    percentage: float


class DemographicsData(BaseModel):
    """Demographics data for charts."""
    age_groups: List[AgeGroup]
    gender_distribution: List[GenderDistribution]
    total_people: int


class ChartQueryParams(BaseModel):
    """Query parameters for chart endpoints."""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    granularity: str = "week"  # day, week, month


class SummaryStats(BaseModel):
    """Dashboard summary statistics."""
    total_people: int
    total_checkins: int
    checkins_this_week: int
    checkins_last_week: int
    week_over_week_change: float
    most_popular_event: Optional[str] = None


class ChartResponse(BaseModel):
    """Generic chart response wrapper."""
    data: list
    metadata: Optional[dict] = None
