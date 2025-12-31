"""API routes."""
from fastapi import APIRouter
from app.api import auth, tenant, data, charts, viewer

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(tenant.router, prefix="/tenant", tags=["Tenant"])
api_router.include_router(data.router, prefix="/data", tags=["Data"])
api_router.include_router(charts.router, prefix="/charts", tags=["Charts"])
api_router.include_router(viewer.router, prefix="/viewer", tags=["Data Viewer"])
