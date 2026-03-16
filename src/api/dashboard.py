

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from models.models import User
from schemas.dashboard_schema import (
    TotalProductsResponse,
    TotalWarehousesResponse,
    TotalTransactionsResponse,
    AllTransactionsResponse,
    StockByProductResponse,
    LowStockProductsResponse,
)
from core.dependencies import get_dashboard_service,get_current_user
from services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/total-products", response_model=TotalProductsResponse)
async def get_total_products(
    current_user: Annotated[User, Depends(get_current_user)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> TotalProductsResponse:
    """
    Get total number of products in the tenant's inventory.
    
    - **current_user**: The currently authenticated user (admin or regular).
    """
    return await dashboard_service.get_total_products(current_user.tenant_id)


@router.get("/total-warehouses", response_model=TotalWarehousesResponse)
async def get_total_warehouses(
    current_user: Annotated[User, Depends(get_current_user)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> TotalWarehousesResponse:
    """
    Get total number of warehouses for the tenant.
    
    - **current_user**: The currently authenticated user (admin or regular).
    """
    return await dashboard_service.get_total_warehouses(current_user.tenant_id)


@router.get("/total-transactions", response_model=TotalTransactionsResponse)
async def get_total_transactions(
    current_user: Annotated[User, Depends(get_current_user)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> TotalTransactionsResponse:
    """
    Get total number of inventory transactions for the tenant.
    
    - **current_user**: The currently authenticated user (admin or regular).
    """
    return await dashboard_service.get_total_transactions(current_user.tenant_id)


@router.get("/transactions", response_model=AllTransactionsResponse)
async def get_all_transactions(
    current_user: Annotated[User, Depends(get_current_user)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> AllTransactionsResponse:
    """
    Get all transaction records for the tenant with pagination.
    
    - **current_user**: The currently authenticated user (admin or regular).
    - **limit**: Maximum number of records to return (default: 100, max: 1000).
    - **offset**: Number of records to skip (default: 0).
    """
    return await dashboard_service.get_all_transactions(
        current_user.tenant_id, limit, offset
    )


@router.get("/stock-by-product", response_model=StockByProductResponse)
async def get_stock_by_product(
    current_user: Annotated[User, Depends(get_current_user)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> StockByProductResponse:
    """
    Get stock levels aggregated by product across all warehouses.
    
    - **current_user**: The currently authenticated user (admin or regular).
    """
    return await dashboard_service.get_stock_by_product(current_user.tenant_id)


@router.get("/low-stock-products", response_model=LowStockProductsResponse)
async def get_low_stock_products(
    current_user: Annotated[User, Depends(get_current_user)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> LowStockProductsResponse:
    """
    Get products at or below reorder point.
    Critical for inventory management alerts.
    
    - **current_user**: The currently authenticated user (admin or regular).
    """
    return await dashboard_service.get_low_stock_products(current_user.tenant_id)