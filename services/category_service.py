"""
Category Service - Business logic for category management operations.
"""

from __future__ import annotations

import asyncpg
from fastapi import HTTPException, status

from models.models import User, UserRole, Category
from repositories.interfaces import ICategoryRepository
from repositories.category_repository import CategoryRepository
from schemas.category_schema import (
    CategoryCreateRequest,
    CategoryUpdateRequest,
    CategoryResponse,
    CategoryListResponse,
    CategoryProductPercentage,
    CategoryProductPercentageResponse,
)


class CategoryService:
    """Service class for category management operations."""

    def __init__(self, conn: asyncpg.Connection, category_repo: ICategoryRepository = None):
        self._category_repo = category_repo or CategoryRepository(conn)

    @staticmethod
    def validate_admin_role(user: User):
        """Ensure the user has Admin role, otherwise raise exception."""
        if user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required for this operation",
            )

    async def create_category(
        self, data: CategoryCreateRequest, current_user: User
    ) -> CategoryResponse:
        """
        Create a new category (Admin only).
        
        Args:
            data: Category creation request data
            current_user: The authenticated user
            
        Returns:
            CategoryResponse with created category information
            
        Raises:
            HTTPException: If parent category not found or user lacks permissions
        """
        # Only admins can create categories
        self.validate_admin_role(current_user)

        # If parent_id provided, verify it exists
        if data.parent_id:
            parent = await self._category_repo.get_by_id(
                category_id=data.parent_id, tenant_id=current_user.tenant_id
            )
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Parent category with ID {data.parent_id} not found",
                )

        category = await self._category_repo.create(
            tenant_id=current_user.tenant_id,
            name=data.name,
            parent_id=data.parent_id,
        )

        return CategoryResponse.from_category(category)

    async def get_category_by_id(
        self, category_id: int, current_user: User
    ) -> CategoryResponse:
        """
        Get a category by ID.
        
        Args:
            category_id: Category ID
            current_user: The authenticated user
            
        Returns:
            CategoryResponse with category information
            
        Raises:
            HTTPException: If category not found
        """
        category = await self._category_repo.get_by_id(
            category_id=category_id, tenant_id=current_user.tenant_id
        )

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found",
            )

        return CategoryResponse.from_category(category)

    async def list_categories(
        self, current_user: User, parent_id: int | None = None, roots_only: bool = False
    ) -> CategoryListResponse:
        """
        List categories in the tenant with optional filtering.
        
        Args:
            current_user: The authenticated user
            parent_id: Optional - Filter by parent category ID
            roots_only: If True, return only root categories (no parent)
            
        Returns:
            CategoryListResponse with list of categories
        """
        if roots_only:
            categories = await self._category_repo.list_roots(
                tenant_id=current_user.tenant_id
            )
        elif parent_id is not None:
            categories = await self._category_repo.list_children(
                parent_id=parent_id, tenant_id=current_user.tenant_id
            )
        else:
            categories = await self._category_repo.list_by_tenant(
                tenant_id=current_user.tenant_id
            )

        return CategoryListResponse(
            categories=[CategoryResponse.from_category(c) for c in categories],
            total=len(categories),
        )

    async def update_category(
        self, category_id: int, data: CategoryUpdateRequest, current_user: User
    ) -> CategoryResponse:
        """
        Update a category (Admin only).
        
        Args:
            category_id: Category ID to update
            data: Category update request data
            current_user: The authenticated user
            
        Returns:
            CategoryResponse with updated category information
            
        Raises:
            HTTPException: If category not found, parent not found, or lacks permissions
        """
        # Only admins can update categories
        self.validate_admin_role(current_user)

        # Verify category exists
        existing = await self._category_repo.get_by_id(
            category_id=category_id, tenant_id=current_user.tenant_id
        )
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found",
            )

        # If parent_id is being updated, verify it exists and prevent circular reference
        if data.parent_id is not None:
            if data.parent_id == category_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category cannot be its own parent",
                )
            parent = await self._category_repo.get_by_id(
                category_id=data.parent_id, tenant_id=current_user.tenant_id
            )
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Parent category with ID {data.parent_id} not found",
                )

        category = await self._category_repo.update(
            category_id=category_id,
            tenant_id=current_user.tenant_id,
            name=data.name,
            parent_id=data.parent_id,
        )

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found",
            )

        return CategoryResponse.from_category(category)

    async def delete_category(
        self, category_id: int, current_user: User
    ) -> None:
        """
        Delete a category (Admin only).
        
        Args:
            category_id: Category ID to delete
            current_user: The authenticated user
            
        Raises:
            HTTPException: If category not found or has child categories
        """
        # Only admins can delete categories
        self.validate_admin_role(current_user)

        # Check if category has children
        children = await self._category_repo.list_children(
            parent_id=category_id, tenant_id=current_user.tenant_id
        )
        if children:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete category with {len(children)} child categories. Delete or reassign children first.",
            )

        success = await self._category_repo.delete(
            category_id=category_id, tenant_id=current_user.tenant_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found",
            )

    async def get_product_distribution_by_category(
        self, current_user: User
    ) -> CategoryProductPercentageResponse:
        """
        Get product distribution percentages by category.
        
        Args:
            current_user: The authenticated user
            
        Returns:
            CategoryProductPercentageResponse with product counts and percentages
        """
        data = await self._category_repo.get_product_count_by_category(
            tenant_id=current_user.tenant_id
        )

        # Calculate total products
        total_products = sum(row["product_count"] for row in data)

        # Calculate percentages
        distribution = []
        for row in data:
            product_count = row["product_count"]
            percentage = (product_count / total_products * 100) if total_products > 0 else 0.0
            
            distribution.append(
                CategoryProductPercentage(
                    category_id=row["category_id"],
                    category_name=row["category_name"],
                    product_count=product_count,
                    percentage=round(percentage, 2),
                )
            )

        return CategoryProductPercentageResponse(
            distribution=distribution,
            total_products=total_products,
        )
