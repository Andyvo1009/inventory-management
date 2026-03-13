"""
Warehouse endpoints - CRUD operations for warehouses.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from models.models import User
from schemas.warehouse_schema import (
    WarehouseCreateRequest,
    WarehouseUpdateRequest,
    WarehouseResponse,
    WarehouseDetailResponse,
    WarehouseListResponse,
)
from core.dependencies import get_warehouse_service, get_current_user, get_current_admin_user
from services.warehouse_service import WarehouseService

# ─── Configuration ───────────────────────────────────────────────────────────

router = APIRouter(prefix="/api/warehouses", tags=["Warehouses"])


# ─── Endpoints ───────────────────────────────────────────────────────────────


@router.post("/", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    data: WarehouseCreateRequest,
    current_user: Annotated[User, Depends(get_current_admin_user)],
    warehouse_service: Annotated[WarehouseService, Depends(get_warehouse_service)],
) -> WarehouseResponse:
    """
    Create a new warehouse (Admin only).
    
    - **name**: Warehouse name
    - **location**: Optional warehouse location
    
    Requires: Admin role
    """
    return await warehouse_service.create_warehouse(data, current_user)


@router.get("/", response_model=WarehouseListResponse)
async def list_warehouses(
    current_user: Annotated[User, Depends(get_current_user)],
    warehouse_service: Annotated[WarehouseService, Depends(get_warehouse_service)],
) -> WarehouseListResponse:
    """
    List all warehouses for the current tenant with stock summaries.
    
    Each warehouse includes:
    - Basic warehouse information (id, name, location)
    - Total unique products in the warehouse
    - Total stock quantity across all products
    
    Requires: Authentication
    """
    return await warehouse_service.list_warehouses(current_user)


@router.get("/{warehouse_id}", response_model=WarehouseDetailResponse)
async def get_warehouse(
    warehouse_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    warehouse_service: Annotated[WarehouseService, Depends(get_warehouse_service)],
) -> WarehouseDetailResponse:
    """
    Get detailed warehouse information including all products and stock levels.
    
    Returns:
    - Warehouse basic information
    - Total unique products
    - Total stock quantity
    - List of all products with their stock quantities in this warehouse
    
    Requires: Authentication
    """
    return await warehouse_service.get_warehouse_by_id(warehouse_id, current_user)


@router.put("/{warehouse_id}", response_model=WarehouseResponse)
async def update_warehouse(
    warehouse_id: int,
    data: WarehouseUpdateRequest,
    current_user: Annotated[User, Depends(get_current_admin_user)],
    warehouse_service: Annotated[WarehouseService, Depends(get_warehouse_service)],
) -> WarehouseResponse:
    """
    Update an existing warehouse (Admin only).
    
    - **warehouse_id**: The ID of the warehouse to update
    - **name**: Optional - New warehouse name
    - **location**: Optional - New warehouse location
    
    Only provided fields will be updated.
    
    Requires: Admin role
    """
    return await warehouse_service.update_warehouse(warehouse_id, data, current_user)


@router.delete("/{warehouse_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_warehouse(
    warehouse_id: int,
    current_user: Annotated[User, Depends(get_current_admin_user)],
    warehouse_service: Annotated[WarehouseService, Depends(get_warehouse_service)],
):
    """
    Delete a warehouse (Admin only).
    
    - **warehouse_id**: The ID of the warehouse to delete
    
    Warning: This will cascade delete related stock records and transactions.
    
    Requires: Admin role
    """
    await warehouse_service.delete_warehouse(warehouse_id, current_user)
