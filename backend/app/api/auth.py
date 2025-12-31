"""Authentication API endpoints."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Tenant
from app.schemas.auth import UserLogin, UserResponse, Token, SignupRequest
from app.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    encrypt_credential,
    generate_schema_name,
)
from app.dependencies import get_current_user

router = APIRouter()


@router.post("/signup", response_model=Token)
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """
    Create a new tenant (church) and admin user.
    Returns JWT token for immediate login.
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Generate schema name from church name, city, state
    schema_name = generate_schema_name(request.church_name, request.city, request.state)

    # Check if schema already exists
    existing_tenant = db.query(Tenant).filter(Tenant.schema_name == schema_name).first()
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A church with similar name already exists in {request.city}, {request.state}"
        )

    # Create tenant
    tenant = Tenant(
        name=request.church_name,
        city=request.city,
        state=request.state.upper()[:2],
        schema_name=schema_name,
    )

    # Add PCO credentials if provided
    if request.pco_app_id and request.pco_secret:
        tenant.pco_app_id_encrypted = encrypt_credential(request.pco_app_id)
        tenant.pco_secret_encrypted = encrypt_credential(request.pco_secret)

    db.add(tenant)
    db.flush()  # Get tenant ID

    # Create admin user
    user = User(
        tenant_id=tenant.id,
        email=request.email,
        password_hash=get_password_hash(request.password),
        first_name=request.first_name,
        last_name=request.last_name,
        is_admin=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "tenant_id": str(tenant.id),
            "email": user.email,
            "is_admin": user.is_admin,
        }
    )

    return Token(access_token=access_token)


@router.post("/login", response_model=Token)
async def login(request: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id),
            "email": user.email,
            "is_admin": user.is_admin,
        }
    )

    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user's information.
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_admin=current_user.is_admin,
        tenant_id=str(current_user.tenant_id),
        created_at=current_user.created_at,
    )
