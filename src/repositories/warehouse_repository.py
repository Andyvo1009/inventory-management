"""
Warehouse Repository — concrete asyncpg implementation.
"""

from __future__ import annotations

import asyncpg

from models.models import Warehouse
from repositories.interfaces import IWarehouseRepository


class WarehouseRepository(IWarehouseRepository):
    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def create(
        self,
        tenant_id: int,
        name: str,
        location: str | None = None,
    ) -> Warehouse:
        row = await self._conn.fetchrow(
            """
            INSERT INTO warehouses (tenant_id, name, location)
            VALUES ($1, $2, $3)
            RETURNING id, tenant_id, name, location
            """,
            tenant_id,
            name,
            location,
        )
        return Warehouse(**row)

    async def get_by_id(self, warehouse_id: int, tenant_id: int) -> Warehouse | None:
        row = await self._conn.fetchrow(
            """
            SELECT id, tenant_id, name, location
            FROM warehouses
            WHERE id = $1 AND tenant_id = $2
            """,
            warehouse_id,
            tenant_id,
        )
        return Warehouse(**row) if row else None

    async def list_by_tenant(self, tenant_id: int) -> list[Warehouse]:
        rows = await self._conn.fetch(
            """
            SELECT id, tenant_id, name, location
            FROM warehouses
            WHERE tenant_id = $1
            ORDER BY name
            """,
            tenant_id,
        )
        return [Warehouse(**r) for r in rows]

    async def update(
        self,
        warehouse_id: int,
        tenant_id: int,
        name: str | None = None,
        location: str | None = None,
    ) -> Warehouse | None:
        row = await self._conn.fetchrow(
            """
            UPDATE warehouses
            SET
                name     = COALESCE($3, name),
                location = COALESCE($4, location)
            WHERE id = $1 AND tenant_id = $2
            RETURNING id, tenant_id, name, location
            """,
            warehouse_id,
            tenant_id,
            name,
            location,
        )
        return Warehouse(**row) if row else None

    async def delete(self, warehouse_id: int, tenant_id: int) -> bool:
        result = await self._conn.execute(
            "DELETE FROM warehouses WHERE id = $1 AND tenant_id = $2",
            warehouse_id,
            tenant_id,
        )
        return result == "DELETE 1"
