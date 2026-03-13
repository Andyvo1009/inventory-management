"""
Dashboard Service — Business logic for dashboard metrics and analytics.

Coordinates dashboard repository calls and formats data for API responses.
"""

from __future__ import annotations

import asyncpg

from repositories.dashboard_repository import DashboardRepository
from repositories.interfaces import IDashboardRepository
from schemas.dashboard_schema import (
    TotalProductsResponse,
    TotalWarehousesResponse,
    TotalTransactionsResponse,
    AllTransactionsResponse,
    StockByProductResponse,
    LowStockProductsResponse,
)


class DashboardService:
    """Service layer for dashboard operations."""

    def __init__(self, conn: asyncpg.Connection) -> None:
        self._repo: IDashboardRepository = DashboardRepository(conn)

    async def get_total_products(self, tenant_id: int) -> TotalProductsResponse:
        """Get total number of products for a tenant."""
        total = await self._repo.get_total_products(tenant_id)
        return TotalProductsResponse(total_products=total)

    async def get_total_warehouses(self, tenant_id: int) -> TotalWarehousesResponse:
        """Get total number of warehouses for a tenant."""
        total = await self._repo.get_total_warehouses(tenant_id)
        return TotalWarehousesResponse(total_warehouses=total)

    async def get_total_transactions(self, tenant_id: int) -> TotalTransactionsResponse:
        """Get total number of transactions for a tenant."""
        total = await self._repo.get_total_transactions(tenant_id)
        return TotalTransactionsResponse(total_transactions=total)

    async def get_all_transactions(
        self, tenant_id: int, limit: int = 100, offset: int = 0
    ) -> AllTransactionsResponse:
        """Get all transaction records with pagination."""
        transactions = await self._repo.get_all_transactions(tenant_id, limit, offset)
        return AllTransactionsResponse(transactions=transactions)

    async def get_stock_by_product(self, tenant_id: int) -> StockByProductResponse:
        """Get stock levels aggregated by product."""
        stock_data = await self._repo.get_stock_by_product(tenant_id)
        return StockByProductResponse(stock_by_product=stock_data)

    async def get_low_stock_products(self, tenant_id: int) -> LowStockProductsResponse:
        """Get products at or below reorder point."""
        low_stock = await self._repo.get_low_stock_products(tenant_id)
        return LowStockProductsResponse(low_stock_products=low_stock)
