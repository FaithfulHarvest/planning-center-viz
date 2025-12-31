"""Tenant schemas."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TenantResponse(BaseModel):
    """Schema for tenant response."""
    id: str
    name: str
    trial_start_date: datetime
    trial_end_date: datetime
    is_trial_active: bool
    days_remaining: int
    is_locked: bool
    has_credentials: bool
    last_data_refresh: Optional[datetime] = None
    created_at: datetime
    data_timezone: str = 'US/Central'

    class Config:
        from_attributes = True


class TenantUpdate(BaseModel):
    """Schema for updating tenant info."""
    name: Optional[str] = None
    data_timezone: Optional[str] = None


class CredentialsUpdate(BaseModel):
    """Schema for updating PCO credentials."""
    pco_app_id: str
    pco_secret: str


class CredentialsTest(BaseModel):
    """Schema for testing PCO credentials."""
    pco_app_id: str
    pco_secret: str


class CredentialsTestResponse(BaseModel):
    """Response from credentials test."""
    success: bool
    message: str
    services_available: Optional[list[str]] = None
