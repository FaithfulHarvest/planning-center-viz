"""Authentication schemas."""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_admin: bool
    tenant_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class SignupRequest(BaseModel):
    """Schema for church signup (creates tenant + admin user)."""
    # Church info
    church_name: str
    city: str
    state: str  # 2-letter state abbreviation

    # Admin user info
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    # PCO credentials (optional at signup)
    pco_app_id: Optional[str] = None
    pco_secret: Optional[str] = None
