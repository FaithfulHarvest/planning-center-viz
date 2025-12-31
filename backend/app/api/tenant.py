"""Tenant management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.tenant import (
    TenantResponse,
    TenantUpdate,
    CredentialsUpdate,
    CredentialsTest,
    CredentialsTestResponse,
)
from app.security import encrypt_credential, decrypt_credential
from app.dependencies import get_current_user, require_admin
from app.etl.pco_client import PCOClient

router = APIRouter()


@router.get("", response_model=TenantResponse)
async def get_tenant(current_user: User = Depends(get_current_user)):
    """
    Get current tenant information including trial status.
    """
    tenant = current_user.tenant
    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        trial_start_date=tenant.trial_start_date,
        trial_end_date=tenant.trial_end_date,
        is_trial_active=tenant.is_trial_active,
        days_remaining=tenant.days_remaining,
        is_locked=tenant.is_locked,
        has_credentials=tenant.has_credentials,
        last_data_refresh=tenant.last_data_refresh,
        created_at=tenant.created_at,
        data_timezone=tenant.data_timezone,
    )


@router.put("", response_model=TenantResponse)
async def update_tenant(
    request: TenantUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update tenant information. Requires admin access.
    """
    tenant = current_user.tenant

    if request.name:
        tenant.name = request.name

    if request.data_timezone:
        # Validate timezone
        import pytz
        if request.data_timezone in pytz.all_timezones:
            tenant.data_timezone = request.data_timezone
        else:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail=f"Invalid timezone: {request.data_timezone}")

    db.commit()
    db.refresh(tenant)

    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        trial_start_date=tenant.trial_start_date,
        trial_end_date=tenant.trial_end_date,
        is_trial_active=tenant.is_trial_active,
        days_remaining=tenant.days_remaining,
        is_locked=tenant.is_locked,
        has_credentials=tenant.has_credentials,
        last_data_refresh=tenant.last_data_refresh,
        created_at=tenant.created_at,
        data_timezone=tenant.data_timezone,
    )


@router.put("/credentials", response_model=TenantResponse)
async def update_credentials(
    request: CredentialsUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update PCO API credentials. Requires admin access.
    """
    tenant = current_user.tenant

    # Encrypt and store credentials
    tenant.pco_app_id_encrypted = encrypt_credential(request.pco_app_id)
    tenant.pco_secret_encrypted = encrypt_credential(request.pco_secret)

    db.commit()
    db.refresh(tenant)

    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        trial_start_date=tenant.trial_start_date,
        trial_end_date=tenant.trial_end_date,
        is_trial_active=tenant.is_trial_active,
        days_remaining=tenant.days_remaining,
        is_locked=tenant.is_locked,
        has_credentials=tenant.has_credentials,
        last_data_refresh=tenant.last_data_refresh,
        created_at=tenant.created_at,
        data_timezone=tenant.data_timezone,
    )


@router.post("/test-credentials", response_model=CredentialsTestResponse)
async def test_credentials(
    request: CredentialsTest,
    current_user: User = Depends(get_current_user)
):
    """
    Test PCO API credentials without saving them.
    """
    try:
        client = PCOClient(request.pco_app_id, request.pco_secret)
        success, error = client.test_connection()

        if success:
            # Try to get available services
            services = []
            test_services = ["people", "check-ins", "services", "groups", "giving"]
            for service in test_services:
                try:
                    response = client.get(f"/{service}/v2")
                    if response:
                        services.append(service)
                except Exception:
                    pass

            return CredentialsTestResponse(
                success=True,
                message="Successfully connected to Planning Center!",
                services_available=services
            )
        else:
            return CredentialsTestResponse(
                success=False,
                message=f"Connection failed: {error}"
            )
    except Exception as e:
        return CredentialsTestResponse(
            success=False,
            message=f"Error testing credentials: {str(e)}"
        )
