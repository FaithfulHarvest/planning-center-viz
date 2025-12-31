"""Data refresh job model for tracking sync status."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship

from app.database import Base


class DataRefreshJob(Base):
    """Data refresh job model."""

    __tablename__ = "data_refresh_jobs"

    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UNIQUEIDENTIFIER, ForeignKey("tenants.id"), nullable=False)

    # Job status
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Progress tracking
    total_endpoints = Column(Integer, nullable=True)
    completed_endpoints = Column(Integer, default=0)
    current_endpoint = Column(String(255), nullable=True)

    # Results
    records_fetched = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    tenant = relationship("Tenant", back_populates="refresh_jobs")

    def mark_started(self):
        """Mark the job as started."""
        self.status = "running"
        self.started_at = datetime.now(timezone.utc)

    def mark_completed(self, records_fetched: int = 0):
        """Mark the job as completed."""
        self.status = "completed"
        self.completed_at = datetime.now(timezone.utc)
        self.records_fetched = records_fetched

    def mark_failed(self, error_message: str):
        """Mark the job as failed."""
        self.status = "failed"
        self.completed_at = datetime.now(timezone.utc)
        self.error_message = error_message

    def update_progress(self, current_endpoint: str, completed_endpoints: int):
        """Update job progress."""
        self.current_endpoint = current_endpoint
        self.completed_endpoints = completed_endpoints
