"""
Operation Repository - asyncpg data access for operation-first workflow.
"""

from __future__ import annotations

import asyncpg

from models.models import InventoryOperation, OperationStatus, OperationType


class OperationRepository:
    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def create(
        self,
        tenant_id: int,
        operation_type: OperationType,
        status: OperationStatus,
        source_warehouse_id: int | None,
        destination_warehouse_id: int | None,
        reference_code: str | None,
        user_id: int | None,
        note: str | None,
        conn: asyncpg.Connection | None = None,
    ) -> InventoryOperation:
        c = conn or self._conn
        row = await c.fetchrow(
            """
            INSERT INTO inventory_operations
                (tenant_id, user_id, operation_type, status, source_warehouse_id,
                 destination_warehouse_id, reference_code, note)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id, tenant_id, user_id, operation_type, status,
                      source_warehouse_id, destination_warehouse_id,
                      reference_code, note, created_at, updated_at
            """,
            tenant_id,
            user_id,
            operation_type.value,
            status.value,
            source_warehouse_id,
            destination_warehouse_id,
            reference_code,
            note,
        )
        return _row_to_operation(row)

    async def get_by_id(
        self,
        operation_id: int,
        tenant_id: int,
        conn: asyncpg.Connection | None = None,
    ) -> InventoryOperation | None:
        c = conn or self._conn
        row = await c.fetchrow(
            """
            SELECT id, tenant_id, user_id, operation_type, status,
                   source_warehouse_id, destination_warehouse_id,
                   reference_code, note, created_at, updated_at
            FROM inventory_operations
            WHERE id = $1 AND tenant_id = $2
            """,
            operation_id,
            tenant_id,
        )
        return _row_to_operation(row) if row else None

    async def get_by_id_for_update(
        self,
        operation_id: int,
        tenant_id: int,
        conn: asyncpg.Connection | None = None,
    ) -> InventoryOperation | None:
        c = conn or self._conn
        row = await c.fetchrow(
            """
            SELECT id, tenant_id, user_id, operation_type, status,
                   source_warehouse_id, destination_warehouse_id,
                   reference_code, note, created_at, updated_at
            FROM inventory_operations
            WHERE id = $1 AND tenant_id = $2
            FOR UPDATE
            """,
            operation_id,
            tenant_id,
        )
        return _row_to_operation(row) if row else None

    async def update_status(
        self,
        operation_id: int,
        tenant_id: int,
        status: OperationStatus,
        conn: asyncpg.Connection | None = None,
    ) -> InventoryOperation | None:
        c = conn or self._conn
        row = await c.fetchrow(
            """
            UPDATE inventory_operations
            SET status = $3, updated_at = CURRENT_TIMESTAMP
            WHERE id = $1 AND tenant_id = $2
            RETURNING id, tenant_id, user_id, operation_type, status,
                      source_warehouse_id, destination_warehouse_id,
                      reference_code, note, created_at, updated_at
            """,
            operation_id,
            tenant_id,
            status.value,
        )
        return _row_to_operation(row) if row else None

    async def list_by_tenant(
        self,
        tenant_id: int,
        operation_type: OperationType | None,
        status: OperationStatus | None,
        warehouse_id: int | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        rows = await self._conn.fetch(
            """
            SELECT
                o.id,
                o.tenant_id,
                o.operation_type,
                o.status,
                o.source_warehouse_id,
                sw.name AS source_warehouse_name,
                o.destination_warehouse_id,
                dw.name AS destination_warehouse_name,
                o.user_id,
                u.name AS user_name,
                o.reference_code,
                o.note,
                o.created_at,
                o.updated_at
            FROM inventory_operations o
                        LEFT JOIN warehouses sw ON o.source_warehouse_id = sw.id
                        LEFT JOIN warehouses dw ON o.destination_warehouse_id = dw.id
                        LEFT JOIN users u ON o.user_id = u.id
            WHERE o.tenant_id = $1
              AND ($2::TEXT IS NULL OR o.operation_type::TEXT = $2)
              AND ($3::TEXT IS NULL OR o.status::TEXT = $3)
              AND ($4::INTEGER IS NULL
                   OR o.source_warehouse_id = $4
                   OR o.destination_warehouse_id = $4)
            ORDER BY o.created_at DESC
            LIMIT $5 OFFSET $6
            """,
            tenant_id,
            operation_type.value if operation_type else None,
            status.value if status else None,
            warehouse_id,
            limit,
            offset,
        )
        return [dict(r) for r in rows]

    async def get_detailed(
        self,
        operation_id: int,
        tenant_id: int,
    ) -> dict | None:
        header = await self._conn.fetchrow(
            """
            SELECT
                o.id,
                o.tenant_id,
                o.operation_type,
                o.status,
                o.source_warehouse_id,
                sw.name AS source_warehouse_name,
                o.destination_warehouse_id,
                dw.name AS destination_warehouse_name,
                o.user_id,
                u.name AS user_name,
                o.reference_code,
                o.note,
                o.created_at,
                o.updated_at
            FROM inventory_operations o
                        LEFT JOIN warehouses sw ON o.source_warehouse_id = sw.id
                        LEFT JOIN warehouses dw ON o.destination_warehouse_id = dw.id
                        LEFT JOIN users u ON o.user_id = u.id
            WHERE o.id = $1 AND o.tenant_id = $2
            """,
            operation_id,
            tenant_id,
        )
        if not header:
            return None

        item_rows = await self._conn.fetch(
            """
            SELECT
                t.id,
                t.operation_id,
                t.product_id,
                p.name AS product_name,
                p.sku AS product_sku,
                t.type,
                t.warehouse_id,
                w.name AS warehouse_name,
                t.quantity,
                t.movement_status
            FROM inventory_transactions t
                        JOIN products p ON p.id = t.product_id
                        LEFT JOIN warehouses w ON w.id = t.warehouse_id
            WHERE t.operation_id = $1 AND t.tenant_id = $2
            ORDER BY t.id ASC
            """,
            operation_id,
            tenant_id,
        )
        response = dict(header)
        response["items"] = [dict(r) for r in item_rows]
        return response


def _row_to_operation(row: asyncpg.Record) -> InventoryOperation:
    return InventoryOperation(
        id=row["id"],
        tenant_id=row["tenant_id"],
        user_id=row["user_id"],
        operation_type=OperationType(row["operation_type"]),
        status=OperationStatus(row["status"]),
        source_warehouse_id=row["source_warehouse_id"],
        destination_warehouse_id=row["destination_warehouse_id"],
        reference_code=row["reference_code"],
        note=row["note"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
