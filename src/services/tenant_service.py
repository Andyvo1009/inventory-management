"""
Tenant Service - Business logic for tenant profile operations.
"""

from __future__ import annotations

import asyncpg
from fastapi import HTTPException, status

from models.models import User
from repositories.interfaces import ITenantRepository
from repositories.tenant_repository import TenantRepository
from schemas.tenant_schema import TenantResponse


class TenantService:
    """Service class for tenant profile operations."""

    def __init__(self, conn: asyncpg.Connection, tenant_repo: ITenantRepository = None):
        self._tenant_repo = tenant_repo or TenantRepository(conn)

    async def get_current_tenant(self, current_user: User) -> TenantResponse:
        tenant = await self._tenant_repo.get_by_id(current_user.tenant_id)

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found",
            )

        return TenantResponse.from_tenant(tenant)
