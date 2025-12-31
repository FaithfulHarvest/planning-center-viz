"""Data refresh API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import User, DataRefreshJob
from app.dependencies import verify_trial_active
from app.services.data_sync_service import run_data_refresh

router = APIRouter()


class RefreshStatusResponse(BaseModel):
    """Response for refresh status."""
    job_id: str
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    total_endpoints: Optional[int] = None
    completed_endpoints: int = 0
    current_endpoint: Optional[str] = None
    records_fetched: int = 0
    error_message: Optional[str] = None


class RefreshStartResponse(BaseModel):
    """Response when starting a refresh."""
    job_id: str
    status: str
    message: str


@router.post("/refresh", response_model=RefreshStartResponse)
async def start_data_refresh(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(verify_trial_active),
    db: Session = Depends(get_db)
):
    """
    Start a data refresh job. Fetches data from Planning Center and loads to database.
    """
    tenant = current_user.tenant

    # Check if tenant has credentials
    if not tenant.has_credentials:
        raise HTTPException(
            status_code=400,
            detail="Planning Center credentials not configured. Please add your API credentials first."
        )

    # Check if a job is already running
    existing_job = db.query(DataRefreshJob).filter(
        DataRefreshJob.tenant_id == tenant.id,
        DataRefreshJob.status.in_(['pending', 'running'])
    ).first()

    if existing_job:
        raise HTTPException(
            status_code=400,
            detail="A data refresh is already in progress"
        )

    # Create new job
    job = DataRefreshJob(tenant_id=tenant.id)
    db.add(job)
    db.commit()
    db.refresh(job)

    # Start background task
    background_tasks.add_task(
        run_data_refresh,
        job_id=str(job.id),
        tenant_id=str(tenant.id)
    )

    return RefreshStartResponse(
        job_id=str(job.id),
        status="started",
        message="Data refresh started. This may take a few minutes."
    )


@router.get("/refresh/status", response_model=RefreshStatusResponse)
async def get_refresh_status(
    current_user: User = Depends(verify_trial_active),
    db: Session = Depends(get_db)
):
    """
    Get the status of the most recent data refresh job.
    """
    tenant = current_user.tenant

    # Get most recent job
    job = db.query(DataRefreshJob).filter(
        DataRefreshJob.tenant_id == tenant.id
    ).order_by(DataRefreshJob.created_at.desc()).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="No data refresh jobs found"
        )

    return RefreshStatusResponse(
        job_id=str(job.id),
        status=job.status,
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        total_endpoints=job.total_endpoints,
        completed_endpoints=job.completed_endpoints or 0,
        current_endpoint=job.current_endpoint,
        records_fetched=job.records_fetched or 0,
        error_message=job.error_message
    )


@router.get("/refresh/history")
async def get_refresh_history(
    limit: int = 10,
    current_user: User = Depends(verify_trial_active),
    db: Session = Depends(get_db)
):
    """
    Get history of data refresh jobs.
    """
    tenant = current_user.tenant

    jobs = db.query(DataRefreshJob).filter(
        DataRefreshJob.tenant_id == tenant.id
    ).order_by(DataRefreshJob.created_at.desc()).limit(limit).all()

    return [
        RefreshStatusResponse(
            job_id=str(job.id),
            status=job.status,
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            total_endpoints=job.total_endpoints,
            completed_endpoints=job.completed_endpoints or 0,
            current_endpoint=job.current_endpoint,
            records_fetched=job.records_fetched or 0,
            error_message=job.error_message
        )
        for job in jobs
    ]
