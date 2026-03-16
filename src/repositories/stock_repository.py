"""
Stock Repository — concrete asyncpg implementation.
Manages per-warehouse quantity levels and upserts for stock movements.
"""

from __future__ import annotations

import asyncpg

from models.models import Stock
from repositories.interfaces import IStockRepository


class StockRepository(IStockRepository):
    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def get(self, product_id: int, warehouse_id: int) -> Stock | None:
        row = await self._conn.fetchrow(
            """
            SELECT product_id, warehouse_id, quantity
            FROM stocks
            WHERE product_id = $1 AND warehouse_id = $2
            """,
            product_id,
            warehouse_id,
        )
        return Stock(**row) if row else None

    async def list_by_product(self, product_id: int) -> list[Stock]:
        """Get stock levels across all warehouses for a product."""
        rows = await self._conn.fetch(
            """
            SELECT product_id, warehouse_id, quantity
            FROM stocks
            WHERE product_id = $1
            ORDER BY warehouse_id
            """,
            product_id,
        )
        return [Stock(**r) for r in rows]

    async def list_by_warehouse(self, warehouse_id: int) -> list[Stock]:
        """Get all product stock levels within a warehouse."""
        rows = await self._conn.fetch(
            """
            SELECT product_id, warehouse_id, quantity
            FROM stocks
            WHERE warehouse_id = $1
            ORDER BY product_id
            """,
            warehouse_id,
        )
        return [Stock(**r) for r in rows]

    async def get_total_stock(self, product_id: int) -> int:
        """Sum stock across all warehouses for a product."""
        result = await self._conn.fetchval(
            "SELECT COALESCE(SUM(quantity), 0) FROM stocks WHERE product_id = $1",
            product_id,
        )
        return int(result)

    async def increment(
        self,
        product_id: int,
        warehouse_id: int,
        qty: int,
        conn: asyncpg.Connection | None = None,
    ) -> Stock:
        """Add stock (upsert). Use the provided connection for transaction support."""
        c = conn or self._conn
        row = await c.fetchrow(
            """
            INSERT INTO stocks (product_id, warehouse_id, quantity)
            VALUES ($1, $2, $3)
            ON CONFLICT (product_id, warehouse_id)
            DO UPDATE SET quantity = stocks.quantity + EXCLUDED.quantity
            RETURNING product_id, warehouse_id, quantity
            """,
            product_id,
            warehouse_id,
            qty,
        )
        return Stock(**row)

    async def decrement(
        self,
        product_id: int,
        warehouse_id: int,
        qty: int,
        conn: asyncpg.Connection | None = None,
    ) -> Stock:
        """Remove stock. Raises ValueError if insufficient stock."""
        c = conn or self._conn
        
        # First check current stock level
        current_stock = await c.fetchrow(
            "SELECT product_id, warehouse_id, quantity FROM stocks WHERE product_id = $1 AND warehouse_id = $2",
            product_id,
            warehouse_id,
        )
        
        if current_stock is None:
            raise ValueError(
                f"No stock record found for product in this warehouse."
            )
        
        if current_stock["quantity"] < qty:
            raise ValueError(
                f"Insufficient stock: product in this warehouse has {current_stock['quantity']} units left, but {qty} units requested."
            )
        
        # Now perform the decrement
        row = await c.fetchrow(
            """
            UPDATE stocks
            SET quantity = quantity - $3
            WHERE product_id = $1 AND warehouse_id = $2
            RETURNING product_id, warehouse_id, quantity
            """,
            product_id,
            warehouse_id,
            qty,
        )
        return Stock(**row)

    async def set_quantity(
        self,
        product_id: int,
        warehouse_id: int,
        quantity: int,
    ) -> Stock:
        """Force-set a quantity (e.g. for stock-take / correction)."""
        row = await self._conn.fetchrow(
            """
            INSERT INTO stocks (product_id, warehouse_id, quantity)
            VALUES ($1, $2, $3)
            ON CONFLICT (product_id, warehouse_id)
            DO UPDATE SET quantity = EXCLUDED.quantity
            RETURNING product_id, warehouse_id, quantity
            """,
            product_id,
            warehouse_id,
            quantity,
        )
        return Stock(**row)
