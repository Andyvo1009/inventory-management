"""
Tenant endpoints - tenant profile operations.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from core.dependencies import get_current_user, get_tenant_service
from models.models import User
from schemas.tenant_schema import TenantResponse
from services.tenant_service import TenantService


router = APIRouter(prefix="/api/tenants", tags=["Tenants"])


@router.get("/me", response_model=TenantResponse)
async def get_current_tenant_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    tenant_service: Annotated[TenantService, Depends(get_tenant_service)],
) -> TenantResponse:
    """
    Get current tenant profile information.

    Requires: Authentication
    """
    return await tenant_service.get_current_tenant(current_user)
