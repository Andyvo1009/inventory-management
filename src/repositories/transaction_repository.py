"""
Transaction Repository — concrete asyncpg implementation.
Records every stock movement (In / Out / Transfer).

Reporting methods (movement_history, low_stock_report) live in
ReportRepository per the Interface Segregation Principle.
"""

from __future__ import annotations

import asyncpg

from models.models import InventoryTransaction, TransactionStatus, TransactionType
from repositories.interfaces import ITransactionRepository
from schemas.transaction_schema import TransactionResponse


class TransactionRepository(ITransactionRepository):
    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    # ── Write ────────────────────────────────────────────────────────────────

    async def record(
        self,
        tenant_id: int,
        operation_id: int,
        product_id: int,
        warehouse_id: int,
        type: TransactionType,
        quantity: int,
        user_id: int | None = None,
        note: str | None = None,
        conn: asyncpg.Connection | None = None,
    ) -> InventoryTransaction:
        """Insert a transaction log entry."""
        c = conn or self._conn
        row = await c.fetchrow(
            """
            INSERT INTO inventory_transactions
                (tenant_id, operation_id, product_id, user_id, warehouse_id, type, quantity, note)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id, tenant_id, operation_id, product_id, user_id, warehouse_id,
                      type, quantity, note, timestamp, movement_status
            """,
            tenant_id,
            operation_id,
            product_id,
            user_id,
            warehouse_id,
            type.value,
            quantity,
            note,
        )
        return _row_to_transaction(row)

    # ── Read ─────────────────────────────────────────────────────────────────

    async def get_by_id(self, tx_id: int, tenant_id: int) -> InventoryTransaction | None:
        row = await self._conn.fetchrow(
            """
             SELECT id, tenant_id, operation_id, product_id, user_id, warehouse_id,
                 type, quantity, note, timestamp, movement_status
            FROM inventory_transactions
            WHERE id = $1 AND tenant_id = $2
            """,
            tx_id,
            tenant_id,
        )
        return _row_to_transaction(row) if row else None

    async def list_by_tenant(
        self,
        tenant_id: int,
        type: TransactionType | None = None,
        warehouse_id: int | None = None,
        product_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TransactionResponse]:
        """Paginated list of all transactions with joined product, warehouse, and user data."""
        rows = await self._conn.fetch(
            """
            SELECT 
                t.id, 
                t.tenant_id, 
                t.type, 
                t.product_id,
                p.name AS product_name,
                p.sku AS product_sku,
                t.operation_id,
                t.quantity,
                                o.source_warehouse_id AS origin_warehouse_id,
                                ow.name AS origin_warehouse_name,
                                o.destination_warehouse_id AS des_warehouse_id,
                                dw.name AS des_warehouse_name,
                t.user_id,
                u.name AS user_name,
                t.note,
                t.timestamp,
                t.movement_status
            FROM inventory_transactions t
                        JOIN products p ON t.product_id = p.id
                        LEFT JOIN inventory_operations o ON t.operation_id = o.id
                        LEFT JOIN warehouses ow ON o.source_warehouse_id = ow.id
                        LEFT JOIN warehouses dw ON o.destination_warehouse_id = dw.id
                        LEFT JOIN users u ON t.user_id = u.id
            WHERE t.tenant_id = $1
                            AND ($2::TEXT IS NULL OR t.type::TEXT = $2 OR ($2 = 'Transfer' AND o.operation_type::TEXT = 'Transfer'))
                            AND ($3::INTEGER IS NULL OR o.source_warehouse_id = $3 OR o.destination_warehouse_id = $3 OR t.warehouse_id = $3)
              AND ($4::INTEGER IS NULL OR t.product_id = $4)
            ORDER BY t.timestamp DESC
            LIMIT $5 OFFSET $6
            """,
            tenant_id,
            type.value if type else None,
            warehouse_id,
            product_id,
            limit,
            offset,
        )
        return [TransactionResponse(**r) for r in rows]

    async def get_by_id_detailed(self, tx_id: int, tenant_id: int) -> TransactionResponse | None:
        """Get a single transaction with all joined data."""
        row = await self._conn.fetchrow(
            """
            SELECT 
                t.id, 
                t.tenant_id, 
                t.type, 
                t.product_id,
                p.name AS product_name,
                p.sku AS product_sku,
                t.quantity,
                o.source_warehouse_id AS origin_warehouse_id,
                ow.name AS origin_warehouse_name,
                o.destination_warehouse_id AS des_warehouse_id,
                dw.name AS des_warehouse_name,
                t.user_id,
                u.name AS user_name,
                t.note,
                t.timestamp
            FROM inventory_transactions t
                        JOIN products p ON t.product_id = p.id
                        LEFT JOIN inventory_operations o ON t.operation_id = o.id
                        LEFT JOIN warehouses ow ON o.source_warehouse_id = ow.id
                        LEFT JOIN warehouses dw ON o.destination_warehouse_id = dw.id
                        LEFT JOIN users u ON t.user_id = u.id
            WHERE t.id = $1 AND t.tenant_id = $2
            """,
            tx_id,
            tenant_id,
        )
        return TransactionResponse(**row) if row else None

    async def list_by_operation(self, operation_id: int, tenant_id: int) -> list[TransactionResponse]:
        rows = await self._conn.fetch(
            """
            SELECT
                t.id,
                t.tenant_id,
                t.type,
                t.product_id,
                p.name AS product_name,
                p.sku AS product_sku,
                t.quantity,
                o.source_warehouse_id AS origin_warehouse_id,
                ow.name AS origin_warehouse_name,
                o.destination_warehouse_id AS des_warehouse_id,
                dw.name AS des_warehouse_name,
                t.user_id,
                u.name AS user_name,
                t.note,
                t.timestamp
            FROM inventory_transactions t
                        JOIN products p ON t.product_id = p.id
                        LEFT JOIN inventory_operations o ON t.operation_id = o.id
                        LEFT JOIN warehouses ow ON o.source_warehouse_id = ow.id
                        LEFT JOIN warehouses dw ON o.destination_warehouse_id = dw.id
                        LEFT JOIN users u ON t.user_id = u.id
            WHERE t.operation_id = $1 AND t.tenant_id = $2
            ORDER BY t.timestamp DESC, t.id DESC
            """,
            operation_id,
            tenant_id,
        )
        return [TransactionResponse(**r) for r in rows]

    async def list_inventory_by_operation(
        self,
        operation_id: int,
        tenant_id: int,
        conn: asyncpg.Connection | None = None,
    ) -> list[InventoryTransaction]:
        c = conn or self._conn
        rows = await c.fetch(
            """
            SELECT id, tenant_id, operation_id, product_id, user_id, warehouse_id,
                   type, quantity, note, timestamp, movement_status
            FROM inventory_transactions
            WHERE operation_id = $1 AND tenant_id = $2
            ORDER BY id ASC
            """,
            operation_id,
            tenant_id,
        )
        return [_row_to_transaction(r) for r in rows]

    async def update_movement_status_by_operation(
        self,
        operation_id: int,
        tenant_id: int,
        movement_status: TransactionStatus,
        conn: asyncpg.Connection | None = None,
    ) -> None:
        c = conn or self._conn
        await c.execute(
            """
            UPDATE inventory_transactions
            SET movement_status = $3
            WHERE operation_id = $1 AND tenant_id = $2
            """,
            operation_id,
            tenant_id,
            movement_status.value,
        )

    async def update_transaction_status(
        self,
        transaction_id: int,
        tenant_id: int,
        movement_status: TransactionStatus,
        conn: asyncpg.Connection | None = None,
    ) -> InventoryTransaction | None:
        """Update status of a single transaction."""
        c = conn or self._conn
        row = await c.fetchrow(
            """
            UPDATE inventory_transactions
            SET movement_status = $3
            WHERE id = $1 AND tenant_id = $2
            RETURNING id, tenant_id, operation_id, product_id, user_id, warehouse_id,
                      type, quantity, note, timestamp, movement_status
            """,
            transaction_id,
            tenant_id,
            movement_status.value,
        )
        return _row_to_transaction(row) if row else None

    async def update_transaction_quantity_and_note(
        self,
        transaction_id: int,
        tenant_id: int,
        quantity: int,
        note: str | None,
        conn: asyncpg.Connection | None = None,
    ) -> InventoryTransaction | None:
        """Update quantity and note for a transaction line."""
        c = conn or self._conn
        row = await c.fetchrow(
            """
            UPDATE inventory_transactions
            SET quantity = $3,
                note = $4
            WHERE id = $1 AND tenant_id = $2
            RETURNING id, tenant_id, operation_id, product_id, user_id, warehouse_id,
                      type, quantity, note, timestamp, movement_status
            """,
            transaction_id,
            tenant_id,
            quantity,
            note,
        )
        return _row_to_transaction(row) if row else None

    async def check_all_transactions_completed(
        self,
        operation_id: int,
        tenant_id: int,
        conn: asyncpg.Connection | None = None,
    ) -> bool:
        """Check if all transactions for an operation are completed."""
        c = conn or self._conn
        row = await c.fetchval(
            """
            SELECT COUNT(*) = 0 FROM inventory_transactions
            WHERE operation_id = $1 AND tenant_id = $2 
            AND movement_status != $3
            """,
            operation_id,
            tenant_id,
            TransactionStatus.COMPLETED.value,
        )
        return row

    async def check_any_transaction_failed(
        self,
        operation_id: int,
        tenant_id: int,
        conn: asyncpg.Connection | None = None,
    ) -> bool:
        """Check if any transaction for an operation has failed."""
        c = conn or self._conn
        row = await c.fetchval(
            """
            SELECT EXISTS(SELECT 1 FROM inventory_transactions
            WHERE operation_id = $1 AND tenant_id = $2 
            AND movement_status = $3)
            """,
            operation_id,
            tenant_id,
            TransactionStatus.FAILED.value,
        )
        return row

    async def get_transactions_by_type(
        self,
        operation_id: int,
        tenant_id: int,
        transaction_type: TransactionType,
        conn: asyncpg.Connection | None = None,
    ) -> list[InventoryTransaction]:
        """Get all transactions of a specific type for an operation."""
        c = conn or self._conn
        rows = await c.fetch(
            """
            SELECT id, tenant_id, operation_id, product_id, user_id, warehouse_id,
                   type, quantity, note, timestamp, movement_status
            FROM inventory_transactions
            WHERE operation_id = $1 AND tenant_id = $2 AND type = $3
            ORDER BY id ASC
            """,
            operation_id,
            tenant_id,
            transaction_type.value,
        )
        return [_row_to_transaction(r) for r in rows]


def _row_to_transaction(row: asyncpg.Record) -> InventoryTransaction:
    return InventoryTransaction(
        id=row["id"],
        tenant_id=row["tenant_id"],
        operation_id=row.get("operation_id"),
        product_id=row["product_id"],
        user_id=row["user_id"],
        warehouse_id=row.get("warehouse_id"),
        type=TransactionType(row["type"]),
        quantity=row["quantity"],
        note=row["note"],
        timestamp=row["timestamp"],
        movement_status=TransactionStatus(row.get("movement_status", "Draft")),
    )
