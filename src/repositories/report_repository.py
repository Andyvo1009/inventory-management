"""
Report Repository — concrete asyncpg implementation.

Read-only analytics queries, separated from TransactionRepository
per the Interface Segregation Principle (ISP).
"""

from __future__ import annotations

import asyncpg

from models.models import LowStockRow, MovementHistoryRow, TransactionType
from repositories.interfaces import IReportRepository


class ReportRepository(IReportRepository):
    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def movement_history(
        self,
        product_id: int,
        tenant_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[MovementHistoryRow]:
        """
        Ledger of all changes for a specific product, newest first.
        Suitable for the Movement History report.
        """
        rows = await self._conn.fetch(
            """
            SELECT id, type, quantity, warehouse_id,
                   user_id, note, timestamp
            FROM inventory_transactions
            WHERE product_id = $1 AND tenant_id = $2
            ORDER BY timestamp DESC
            LIMIT $3 OFFSET $4
            """,
            product_id,
            tenant_id,
            limit,
            offset,
        )
        return [
            MovementHistoryRow(
                id=r["id"],
                type=TransactionType(r["type"]),
                quantity=r["quantity"],
                warehouse_id=r["warehouse_id"],
                user_id=r["user_id"],
                note=r["note"],
                timestamp=r["timestamp"],
            )
            for r in rows
        ]

    async def low_stock_report(self, tenant_id: int) -> list[LowStockRow]:
        """
        Return all products where total current stock <= reorder_point.
        Aggregates stock across all warehouses.
        """
        rows = await self._conn.fetch(
            """
            SELECT
                p.id            AS product_id,
                p.sku,
                p.name,
                p.reorder_point,
                COALESCE(SUM(s.quantity), 0) AS total_stock
            FROM products p
            LEFT JOIN stocks s ON s.product_id = p.id
            WHERE p.tenant_id = $1
            GROUP BY p.id, p.sku, p.name, p.reorder_point
            HAVING COALESCE(SUM(s.quantity), 0) <= p.reorder_point
            ORDER BY total_stock ASC, p.name
            """,
            tenant_id,
        )
        return [
            LowStockRow(
                product_id=r["product_id"],
                sku=r["sku"],
                name=r["name"],
                reorder_point=r["reorder_point"],
                total_stock=int(r["total_stock"]),
            )
            for r in rows
        ]
