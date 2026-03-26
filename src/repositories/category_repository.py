"""
Category Repository — concrete asyncpg implementation.
Supports hierarchical categories (parent → child) per tenant.
"""

from __future__ import annotations

import asyncpg

from models.models import Category
from repositories.interfaces import ICategoryRepository


class CategoryRepository(ICategoryRepository):
    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def create(
        self,
        tenant_id: int,
        name: str,
        parent_id: int | None = None,
    ) -> Category:
        """Create a category, optionally nested under a parent."""
        row = await self._conn.fetchrow(
            """
            INSERT INTO categories (tenant_id, name, parent_id)
            VALUES ($1, $2, $3)
            RETURNING id, tenant_id, name, parent_id
            """,
            tenant_id,
            name,
            parent_id,
        )
        return Category(**row)

    async def get_by_id(self, category_id: int, tenant_id: int) -> Category | None:
        row = await self._conn.fetchrow(
            """
            SELECT id, tenant_id, name, parent_id
            FROM categories
            WHERE id = $1 AND tenant_id = $2
            """,
            category_id,
            tenant_id,
        )
        return Category(**row) if row else None

    async def list_by_tenant(self, tenant_id: int) -> list[Category]:
        """Return all categories for a tenant, ordered hierarchically (parents first)."""
        rows = await self._conn.fetch(
            """
            SELECT id, tenant_id, name, parent_id
            FROM categories
            WHERE tenant_id = $1
            ORDER BY parent_id NULLS FIRST, name
            """,
            tenant_id,
        )
        return [Category(**r) for r in rows]

    async def list_children(self, parent_id: int, tenant_id: int) -> list[Category]:
        """Return direct children of a given category."""
        rows = await self._conn.fetch(
            """
            SELECT id, tenant_id, name, parent_id
            FROM categories
            WHERE parent_id = $1 AND tenant_id = $2
            ORDER BY name
            """,
            parent_id,
            tenant_id,
        )
        return [Category(**r) for r in rows]

    async def list_roots(self, tenant_id: int) -> list[Category]:
        """Return top-level categories (no parent)."""
        rows = await self._conn.fetch(
            """
            SELECT id, tenant_id, name, parent_id
            FROM categories
            WHERE tenant_id = $1 AND parent_id IS NULL
            ORDER BY name
            """,
            tenant_id,
        )
        return [Category(**r) for r in rows]

    async def update(
        self,
        category_id: int,
        tenant_id: int,
        name: str | None = None,
        parent_id: int | None = None,
    ) -> Category | None:
        row = await self._conn.fetchrow(
            """
            UPDATE categories
            SET
                name      = COALESCE($3, name),
                parent_id = COALESCE($4, parent_id)
            WHERE id = $1 AND tenant_id = $2
            RETURNING id, tenant_id, name, parent_id
            """,
            category_id,
            tenant_id,
            name,
            parent_id,
        )
        return Category(**row) if row else None

    async def delete(self, category_id: int, tenant_id: int) -> bool:
        result = await self._conn.execute(
            "DELETE FROM categories WHERE id = $1 AND tenant_id = $2",
            category_id,
            tenant_id,
        )
        return result == "DELETE 1"

    async def get_product_count_by_category(self, tenant_id: int) -> list[dict]:
        """Get product counts grouped by category, including uncategorized products."""
        rows = await self._conn.fetch(
            """
            SELECT
                c.id AS category_id,
                c.name AS category_name,
                COUNT(p.id) AS product_count
            FROM categories c
                        LEFT JOIN products p ON p.category_id = c.id
            WHERE c.tenant_id = $1
            GROUP BY c.id, c.name
            
            UNION ALL
            
            SELECT
                NULL AS category_id,
                'Uncategorized' AS category_name,
                COUNT(p.id) AS product_count
            FROM products p
            WHERE p.tenant_id = $1 AND p.category_id IS NULL
            
            ORDER BY product_count DESC, category_name
            """,
            tenant_id,
        )
        return [dict(row) for row in rows]
