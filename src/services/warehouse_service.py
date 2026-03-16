"""
Warehouse Service - Business logic for warehouse operations.
"""

from __future__ import annotations

import asyncpg
from fastapi import HTTPException, status

from models.models import User, UserRole
from repositories.interfaces import IWarehouseRepository, IStockRepository
from repositories.warehouse_repository import WarehouseRepository
from repositories.stock_repository import StockRepository
from schemas.warehouse_schema import (
    WarehouseCreateRequest,
    WarehouseUpdateRequest,
    WarehouseResponse,
    WarehouseDetailResponse,
    WarehouseSummaryResponse,
    WarehouseListResponse,
    ProductStockInfo,
)


class WarehouseService:
    """Service class for warehouse operations."""

    def __init__(
        self,
        conn: asyncpg.Connection,
        warehouse_repo: IWarehouseRepository = None,
        stock_repo: IStockRepository = None,
    ):
        self._conn = conn
        self._warehouse_repo = warehouse_repo or WarehouseRepository(conn)
        self._stock_repo = stock_repo or StockRepository(conn)

    @staticmethod
    def validate_admin_role(user: User):
        """Ensure the user has Admin role, otherwise raise exception."""
        if user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required for this operation",
            )

    async def create_warehouse(
        self, data: WarehouseCreateRequest, current_user: User
    ) -> WarehouseResponse:
        """
        Create a new warehouse (Admin only).
        
        Args:
            data: Warehouse creation request data
            current_user: The authenticated user
            
        Returns:
            WarehouseResponse with created warehouse information
            
        Raises:
            HTTPException: If user lacks permissions
        """
        # Only admins can create warehouses
        self.validate_admin_role(current_user)

        # Create the warehouse
        warehouse = await self._warehouse_repo.create(
            tenant_id=current_user.tenant_id,
            name=data.name,
            location=data.location,
        )

        return WarehouseResponse.from_warehouse(warehouse)

    async def get_warehouse_by_id(
        self, warehouse_id: int, current_user: User
    ) -> WarehouseDetailResponse:
        """
        Get detailed warehouse information including stock data.
        
        Args:
            warehouse_id: Warehouse ID
            current_user: The authenticated user
            
        Returns:
            WarehouseDetailResponse with warehouse and stock information
            
        Raises:
            HTTPException: If warehouse not found
        """
        warehouse = await self._warehouse_repo.get_by_id(
            warehouse_id=warehouse_id, tenant_id=current_user.tenant_id
        )

        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Warehouse with ID {warehouse_id} not found",
            )

        # Get stock information with product details
        rows = await self._conn.fetch(
            """
            SELECT 
                s.product_id,
                p.sku,
                p.name as product_name,
                c.name AS category_name,
                s.quantity
            FROM stocks s
            JOIN products p ON s.product_id = p.id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE s.warehouse_id = $1 AND p.tenant_id = $2
            ORDER BY p.name
            """,
            warehouse_id,
            current_user.tenant_id,
        )

        products = [ProductStockInfo(**row) for row in rows]
        total_unique_products = len(products)
        total_stock = sum(p.quantity for p in products)

        return WarehouseDetailResponse(
            id=warehouse.id,
            tenant_id=warehouse.tenant_id,
            name=warehouse.name,
            location=warehouse.location,
            total_unique_products=total_unique_products,
            total_stock=total_stock,
            products=products,
        )

    async def list_warehouses(
        self, current_user: User
    ) -> WarehouseListResponse:
        """
        List all warehouses with summary stock information.
        
        Args:
            current_user: The authenticated user
            
        Returns:
            WarehouseListResponse with list of warehouses and their stock summaries
        """
        warehouses = await self._warehouse_repo.list_by_tenant(
            tenant_id=current_user.tenant_id
        )

        # Get stock summaries for all warehouses
        warehouse_summaries = []
        for warehouse in warehouses:
            # Get stock summary for this warehouse
            stock_summary = await self._conn.fetchrow(
                """
                SELECT 
                    COUNT(DISTINCT s.product_id) AS total_unique_products,
                    COALESCE(SUM(s.quantity), 0) AS total_stock
                FROM stocks s
                JOIN products p ON s.product_id = p.id
                WHERE s.warehouse_id = $1 AND p.tenant_id = $2
                """,
                warehouse.id,
                current_user.tenant_id,
            )

            warehouse_summaries.append(
                WarehouseSummaryResponse(
                    id=warehouse.id,
                    tenant_id=warehouse.tenant_id,
                    name=warehouse.name,
                    location=warehouse.location,
                    total_unique_products=stock_summary["total_unique_products"],
                    total_stock=stock_summary["total_stock"],
                )
            )

        return WarehouseListResponse(
            warehouses=warehouse_summaries,
            total=len(warehouse_summaries),
        )

    async def update_warehouse(
        self, warehouse_id: int, data: WarehouseUpdateRequest, current_user: User
    ) -> WarehouseResponse:
        """
        Update an existing warehouse (Admin only).
        
        Args:
            warehouse_id: Warehouse ID to update
            data: Warehouse update request data
            current_user: The authenticated user
            
        Returns:
            WarehouseResponse with updated warehouse information
            
        Raises:
            HTTPException: If warehouse not found or user lacks permissions
        """
        # Only admins can update warehouses
        self.validate_admin_role(current_user)

        # Update the warehouse
        warehouse = await self._warehouse_repo.update(
            warehouse_id=warehouse_id,
            tenant_id=current_user.tenant_id,
            name=data.name,
            location=data.location,
        )

        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Warehouse with ID {warehouse_id} not found",
            )

        return WarehouseResponse.from_warehouse(warehouse)

    async def delete_warehouse(
        self, warehouse_id: int, current_user: User
    ) -> None:
        """
        Delete a warehouse (Admin only).
        
        Args:
            warehouse_id: Warehouse ID to delete
            current_user: The authenticated user
            
        Raises:
            HTTPException: If warehouse not found or user lacks permissions
        """
        # Only admins can delete warehouses
        self.validate_admin_role(current_user)

        success = await self._warehouse_repo.delete(
            warehouse_id=warehouse_id, tenant_id=current_user.tenant_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Warehouse with ID {warehouse_id} not found",
            )
