"""
Transaction Repository — concrete asyncpg implementation.
Records every stock movement (In / Out / Transfer).

Reporting methods (movement_history, low_stock_report) live in
ReportRepository per the Interface Segregation Principle.
"""

from __future__ import annotations

import asyncpg

from models.models import InventoryTransaction, TransactionType
from repositories.interfaces import ITransactionRepository
from schemas.transaction_schema import TransactionResponse


class TransactionRepository(ITransactionRepository):
    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    # ── Write ────────────────────────────────────────────────────────────────

    async def record(
        self,
        tenant_id: int,
        product_id: int,
        type: TransactionType,
        quantity: int,
        origin_warehouse_id: int | None = None,
        des_warehouse_id: int | None = None,
        user_id: int | None = None,
        notes: str | None = None,
        conn: asyncpg.Connection | None = None,
    ) -> InventoryTransaction:
        """Insert a transaction log entry."""
        c = conn or self._conn
        row = await c.fetchrow(
            """
            INSERT INTO inventory_transactions
                (tenant_id, product_id, user_id, origin_warehouse_id, des_warehouse_id, type, quantity, notes)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id, tenant_id, product_id, user_id, origin_warehouse_id,
                      des_warehouse_id, type, quantity, notes, timestamp
            """,
            tenant_id,
            product_id,
            user_id,
            origin_warehouse_id,
            des_warehouse_id,
            type.value,
            quantity,
            notes,
        )
        return _row_to_transaction(row)

    # ── Read ─────────────────────────────────────────────────────────────────

    async def get_by_id(self, tx_id: int, tenant_id: int) -> InventoryTransaction | None:
        row = await self._conn.fetchrow(
            """
            SELECT id, tenant_id, product_id, user_id, origin_warehouse_id,
                   des_warehouse_id, type, quantity, notes, timestamp
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
                t.quantity,
                t.origin_warehouse_id,
                ow.name AS origin_warehouse_name,
                t.des_warehouse_id,
                dw.name AS des_warehouse_name,
                t.user_id,
                u.name AS user_name,
                t.notes,
                t.timestamp
            FROM inventory_transactions t
            JOIN products p ON t.product_id = p.id
            LEFT JOIN warehouses ow ON t.origin_warehouse_id = ow.id
            LEFT JOIN warehouses dw ON t.des_warehouse_id = dw.id
            LEFT JOIN users u ON t.user_id = u.id
            WHERE t.tenant_id = $1
              AND ($2::transaction_type IS NULL OR t.type = $2)
              AND ($3::INTEGER IS NULL OR t.origin_warehouse_id = $3 OR t.des_warehouse_id = $3)
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
                t.origin_warehouse_id,
                ow.name AS origin_warehouse_name,
                t.des_warehouse_id,
                dw.name AS des_warehouse_name,
                t.user_id,
                u.name AS user_name,
                t.notes,
                t.timestamp
            FROM inventory_transactions t
            JOIN products p ON t.product_id = p.id
            LEFT JOIN warehouses ow ON t.origin_warehouse_id = ow.id
            LEFT JOIN warehouses dw ON t.des_warehouse_id = dw.id
            LEFT JOIN users u ON t.user_id = u.id
            WHERE t.id = $1 AND t.tenant_id = $2
            """,
            tx_id,
            tenant_id,
        )
        return TransactionResponse(**row) if row else None


def _row_to_transaction(row: asyncpg.Record) -> InventoryTransaction:
    return InventoryTransaction(
        id=row["id"],
        tenant_id=row["tenant_id"],
        product_id=row["product_id"],
        user_id=row["user_id"],
        origin_warehouse_id=row.get("origin_warehouse_id"),
        des_warehouse_id=row.get("des_warehouse_id"),
        type=TransactionType(row["type"]),
        quantity=row["quantity"],
        notes=row["notes"],
        timestamp=row["timestamp"],
    )
