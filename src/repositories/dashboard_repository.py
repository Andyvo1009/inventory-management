"""
Dashboard Repository — concrete asyncpg implementation.

Read-only queries for dashboard metrics and aggregations.
Uses database views: vw_tenant_product_counts, vw_tenant_warehouse_counts,
and vw_tenant_transaction_counts for efficient aggregation.
"""

from __future__ import annotations

import asyncpg

from repositories.interfaces import IDashboardRepository


class DashboardRepository(IDashboardRepository):
    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def get_total_products(self, tenant_id: int) -> int:
        """Get total number of products for a tenant using the view."""
        row = await self._conn.fetchrow(
            """
            SELECT product_count AS total_products
            FROM vw_tenant_product_counts
            WHERE tenant_id = $1
            """,
            tenant_id,
        )
        return row["total_products"] if row else 0

    async def get_total_warehouses(self, tenant_id: int) -> int:
        """Get total number of warehouses for a tenant using the view."""
        row = await self._conn.fetchrow(
            """
            SELECT warehouse_count AS total_warehouses
            FROM vw_tenant_warehouse_counts
            WHERE tenant_id = $1
            """,
            tenant_id,
        )
        return row["total_warehouses"] if row else 0

    async def get_total_transactions(self, tenant_id: int) -> int:
        """Get total number of transactions for a tenant using the view."""
        row = await self._conn.fetchrow(
            """
            SELECT transaction_count AS total_transactions
            FROM vw_tenant_transaction_counts
            WHERE tenant_id = $1
            """,
            tenant_id,
        )
        return row["total_transactions"] if row else 0

    async def get_all_transactions(
        self, tenant_id: int, limit: int = 100, offset: int = 0
    ) -> list[dict]:
        """
        Get all transaction records for a tenant with pagination.
        Returns transaction details with product and warehouse info.
        """
        rows = await self._conn.fetch(
            """
            SELECT
                t.id,
                t.type,
                t.quantity,
                t.timestamp,
                p.name AS product_name,
                p.sku AS product_sku,
                ow.name AS origin_warehouse_name,
                dw.name AS des_warehouse_name
            FROM inventory_transactions t
                        LEFT JOIN products p ON t.product_id = p.id
                        LEFT JOIN inventory_operations o ON t.operation_id = o.id
                        LEFT JOIN warehouses ow ON o.source_warehouse_id = ow.id
                        LEFT JOIN warehouses dw ON o.destination_warehouse_id = dw.id
            WHERE t.tenant_id = $1
            ORDER BY t.timestamp DESC
            LIMIT $2 OFFSET $3
            """,
            tenant_id,
            limit,
            offset,
        )
        return [dict(row) for row in rows]

    async def get_stock_by_product(self, tenant_id: int) -> list[dict]:
        """
        Get stock levels aggregated by product across all warehouses.
        Useful for displaying product inventory overview.
        """
        rows = await self._conn.fetch(
            """
            SELECT
                p.id AS product_id,
                p.sku,
                p.name AS product_name,
                COALESCE(SUM(s.quantity), 0) AS total_stock
            FROM products p
            LEFT JOIN stocks s ON s.product_id = p.id
            WHERE p.tenant_id = $1
            GROUP BY p.id, p.sku, p.name
            ORDER BY p.name
            """,
            tenant_id,
        )
        return [dict(row) for row in rows]

    async def get_low_stock_products(self, tenant_id: int) -> list[dict]:
        """
        Get products where total stock is at or below reorder point.
        Critical for inventory management alerts.
        """
        rows = await self._conn.fetch(
            """
            SELECT
                p.id AS product_id,
                p.sku,
                p.name AS product_name,
                COALESCE(SUM(s.quantity), 0) AS total_stock
            FROM products p
            LEFT JOIN stocks s ON s.product_id = p.id
            WHERE p.tenant_id = $1
            GROUP BY p.id, p.sku, p.name
            HAVING COALESCE(SUM(s.quantity), 0) <= p.reorder_point
            ORDER BY total_stock ASC, p.name
            """,
            tenant_id,
        )
        return [dict(row) for row in rows]
