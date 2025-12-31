"""Tenant model representing a church organization."""
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship

from app.database import Base
from app.config import get_settings

settings = get_settings()


class Tenant(Base):
    """Tenant (church) model."""

    __tablename__ = "tenants"

    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(2), nullable=False)  # 2-letter abbreviation
    schema_name = Column(String(100), nullable=False, unique=True)  # SQL schema name

    # Planning Center credentials (encrypted)
    pco_app_id_encrypted = Column(String(500), nullable=True)
    pco_secret_encrypted = Column(String(500), nullable=True)

    # Data settings
    data_timezone = Column(String(50), default='US/Central', nullable=False)

    # Trial management
    trial_start_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    trial_end_date = Column(DateTime, nullable=False)
    is_locked = Column(Boolean, default=False)

    # Metadata
    last_data_refresh = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    refresh_jobs = relationship("DataRefreshJob", back_populates="tenant", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """Initialize tenant with trial end date."""
        super().__init__(**kwargs)
        if not self.trial_end_date:
            self.trial_end_date = datetime.now(timezone.utc) + timedelta(days=settings.trial_duration_days)

    @property
    def is_trial_active(self) -> bool:
        """Check if the trial is still active."""
        if self.is_locked:
            return False
        return datetime.now(timezone.utc) < self.trial_end_date.replace(tzinfo=timezone.utc)

    @property
    def days_remaining(self) -> int:
        """Get the number of days remaining in the trial."""
        if self.is_locked:
            return 0
        delta = self.trial_end_date.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)
        return max(0, delta.days)

    @property
    def has_credentials(self) -> bool:
        """Check if PCO credentials are configured."""
        return bool(self.pco_app_id_encrypted and self.pco_secret_encrypted)
