"""
Product Repository — concrete asyncpg implementation.
"""

from __future__ import annotations

import asyncpg

from models.models import Product
from repositories.interfaces import IProductRepository
from schemas.product_schema import ProductResponse


class ProductRepository(IProductRepository):
    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def create(
        self,
        tenant_id: int,
        sku: str,
        name: str,
        description: str | None = None,
        category_id: int | None = None,
        reorder_point: int = 0,
    ) -> Product:
        row = await self._conn.fetchrow(
            """
            INSERT INTO products (tenant_id, sku, name, description, category_id, reorder_point)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, tenant_id, category_id, sku, name, description, reorder_point
            """,
            tenant_id,
            sku,
            name,
            description,
            category_id,
            reorder_point,
        )
        return Product(**row)

    async def get_by_id(self, product_id: int, tenant_id: int) -> ProductResponse | None:
        row = await self._conn.fetchrow(
            """
            SELECT p.id, p.tenant_id, p.category_id, p.sku, p.name, p.description, p.reorder_point, c.name AS category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = $1 AND p.tenant_id = $2
            """,
            product_id,
            tenant_id,
        )
        return ProductResponse(**row) if row else None

    async def get_by_sku(self, sku: str, tenant_id: int) -> Product | None:
        row = await self._conn.fetchrow(
            """
            SELECT id, tenant_id, category_id, sku, name, description, reorder_point
            FROM products
            WHERE sku = $1 AND tenant_id = $2
            """,
            sku,
            tenant_id,
        )
        return Product(**row) if row else None

    async def list_by_tenant(
        self,
        tenant_id: int,
        category_id: int | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ProductResponse]:
        """List products with optional category filter and name/SKU search."""
        rows = await self._conn.fetch(
            """
            SELECT p.id, p.tenant_id, p.category_id, p.sku, p.name, p.description, p.reorder_point, c.name AS category_name
            FROM products p
            left join categories c on p.category_id = c.id
            WHERE p.tenant_id = $1
              AND ($2::INTEGER IS NULL OR p.category_id = $2)
              AND ($3::TEXT IS NULL OR p.name ILIKE '%' || $3 || '%' OR p.sku ILIKE '%' || $3 || '%')
            ORDER BY p.name
            LIMIT $4 OFFSET $5
            """,
            tenant_id,
            category_id,
            search,
            limit,
            offset,
        )
        return [ProductResponse(**r) for r in rows]

    async def update(
        self,
        product_id: int,
        tenant_id: int,
        name: str | None = None,
        description: str | None = None,
        category_id: int | None = None,
        reorder_point: int | None = None,
    ) -> Product | None:
        """Staff cannot call this; enforce at the service/API layer."""
        row = await self._conn.fetchrow(
            """
            UPDATE products
            SET
                name          = COALESCE($3, name),
                description   = COALESCE($4, description),
                category_id   = COALESCE($5, category_id),
                reorder_point = COALESCE($6, reorder_point)
            WHERE id = $1 AND tenant_id = $2
            RETURNING id, tenant_id, category_id, sku, name, description, reorder_point
            """,
            product_id,
            tenant_id,
            name,
            description,
            category_id,
            reorder_point,
        )
        return Product(**row) if row else None

    async def delete(self, product_id: int, tenant_id: int) -> bool:
        """Admin only — enforce at the service/API layer."""
        result = await self._conn.execute(
            "DELETE FROM products WHERE id = $1 AND tenant_id = $2",
            product_id,
            tenant_id,
        )
        return result == "DELETE 1"
