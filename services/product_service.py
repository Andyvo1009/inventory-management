"""
Product Service - Business logic for product operations.
"""

from __future__ import annotations

import asyncpg
from fastapi import HTTPException, status

from models.models import User, UserRole
from repositories.interfaces import IProductRepository
from repositories.product_repository import ProductRepository
from schemas.product_schema import (
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductListRequest,
    ProductResponse,
    ProductListResponse,
)


class ProductService:
    """Service class for product operations."""

    def __init__(self, conn: asyncpg.Connection, product_repo: IProductRepository = None):
        self._product_repo = product_repo or ProductRepository(conn)

    @staticmethod
    def validate_admin_role(user: User):
        """Ensure the user has Admin role, otherwise raise exception."""
        if user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required for this operation",
            )

    async def create_product(
        self, data: ProductCreateRequest, current_user: User
    ) -> ProductResponse:
        """
        Create a new product (Admin only).
        
        Args:
            data: Product creation request data
            current_user: The authenticated user
            
        Returns:
            ProductResponse with created product information
            
        Raises:
            HTTPException: If SKU already exists or user lacks permissions
        """
        # Only admins can create products
        self.validate_admin_role(current_user)

        # Check if SKU already exists for this tenant
        existing_product = await self._product_repo.get_by_sku(
            sku=data.sku, tenant_id=current_user.tenant_id
        )
        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with SKU '{data.sku}' already exists",
            )

        # Create the product
        product = await self._product_repo.create(
            tenant_id=current_user.tenant_id,
            sku=data.sku,
            name=data.name,
            description=data.description,
            category_id=data.category_id,
            reorder_point=data.reorder_point,
        )

        return ProductResponse.from_product(product)

    async def get_product_by_id(
        self, product_id: int, current_user: User
    ) -> ProductResponse:
        """
        Get a product by ID.
        
        Args:
            product_id: Product ID
            current_user: The authenticated user
            
        Returns:
            ProductResponse with product information
            
        Raises:
            HTTPException: If product not found
        """
        product = await self._product_repo.get_by_id(
            product_id=product_id, tenant_id=current_user.tenant_id
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found",
            )

        return product

    async def list_products(
        self, filters: ProductListRequest, current_user: User
    ) -> ProductListResponse:
        """
        List products with optional filters.
        
        Args:
            filters: Filtering and pagination parameters
            current_user: The authenticated user
            
        Returns:
            ProductListResponse with list of products
        """
        products = await self._product_repo.list_by_tenant(
            tenant_id=current_user.tenant_id,
            category_id=filters.category_id,
            search=filters.search,
            limit=filters.limit,
            offset=filters.offset,
        )

        return ProductListResponse(
            products=products,
            total=len(products),
            limit=filters.limit,
            offset=filters.offset,
        )

    async def update_product(
        self, product_id: int, data: ProductUpdateRequest, current_user: User
    ) -> ProductResponse:
        """
        Update an existing product (Admin only).
        
        Args:
            product_id: Product ID to update
            data: Product update request data
            current_user: The authenticated user
            
        Returns:
            ProductResponse with updated product information
            
        Raises:
            HTTPException: If product not found or user lacks permissions
        """
        # Only admins can update products
        self.validate_admin_role(current_user)

        # Update the product
        product = await self._product_repo.update(
            product_id=product_id,
            tenant_id=current_user.tenant_id,
            name=data.name,
            description=data.description,
            category_id=data.category_id,
            reorder_point=data.reorder_point,
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found",
            )

        return ProductResponse.from_product(product)

    async def delete_product(
        self, product_id: int, current_user: User
    ) -> None:
        """
        Delete a product (Admin only).
        
        Args:
            product_id: Product ID to delete
            current_user: The authenticated user
            
        Raises:
            HTTPException: If product not found or user lacks permissions
        """
        # Only admins can delete products
        self.validate_admin_role(current_user)

        success = await self._product_repo.delete(
            product_id=product_id, tenant_id=current_user.tenant_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found",
            )
