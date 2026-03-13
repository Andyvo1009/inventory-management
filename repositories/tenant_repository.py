"""
Tenant Repository — concrete asyncpg implementation.
"""

from __future__ import annotations

import asyncpg

from models.models import Tenant
from repositories.interfaces import ITenantRepository


class TenantRepository(ITenantRepository):
    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def create(self, name: str) -> Tenant:
        """Register a new company (tenant)."""
        row = await self._conn.fetchrow(
            """
            INSERT INTO tenants (name)
            VALUES ($1)
            RETURNING id, name, created_at
            """,
            name,
        )
        return Tenant(**row)

    async def get_by_id(self, tenant_id: int) -> Tenant | None:
        row = await self._conn.fetchrow(
            "SELECT id, name, created_at FROM tenants WHERE id = $1",
            tenant_id,
        )
        return Tenant(**row) if row else None

    async def get_by_name(self, name: str) -> Tenant | None:
        row = await self._conn.fetchrow(
            "SELECT id, name, created_at FROM tenants WHERE name = $1",
            name,
        )
        return Tenant(**row) if row else None

    async def list_all(self) -> list[Tenant]:
        rows = await self._conn.fetch(
            "SELECT id, name, created_at FROM tenants ORDER BY created_at DESC"
        )
        return [Tenant(**r) for r in rows]

    async def update(self, tenant_id: int, name: str) -> Tenant | None:
        row = await self._conn.fetchrow(
            """
            UPDATE tenants SET name = $1
            WHERE id = $2
            RETURNING id, name, created_at
            """,
            name,
            tenant_id,
        )
        return Tenant(**row) if row else None

    async def delete(self, tenant_id: int) -> bool:
        result = await self._conn.execute(
            "DELETE FROM tenants WHERE id = $1", tenant_id
        )
        return result == "DELETE 1"
