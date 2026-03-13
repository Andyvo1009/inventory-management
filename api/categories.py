"""
Category endpoints - CRUD operations for categories.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status, Query

from models.models import User
from schemas.category_schema import (
    CategoryCreateRequest,
    CategoryUpdateRequest,
    CategoryResponse,
    CategoryListResponse,
    CategoryProductPercentageResponse,
)
from core.dependencies import get_category_service, get_current_user, get_current_admin_user
from services.category_service import CategoryService

# ─── Configuration ───────────────────────────────────────────────────────────

router = APIRouter(prefix="/api/categories", tags=["Categories"])


# ─── Endpoints ───────────────────────────────────────────────────────────────


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreateRequest,
    current_user: Annotated[User, Depends(get_current_admin_user)],
    category_service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryResponse:
    """
    Create a new category (Admin only).
    
    - **name**: Category name
    - **parent_id**: Optional - Parent category ID for hierarchical structure
    
    Requires: Admin role
    """
    return await category_service.create_category(data, current_user)


@router.get("/", response_model=CategoryListResponse)
async def list_categories(
    current_user: Annotated[User, Depends(get_current_user)],
    category_service: Annotated[CategoryService, Depends(get_category_service)],
    parent_id: Annotated[int | None, Query(description="Filter by parent category ID")] = None,
    roots_only: Annotated[bool, Query(description="Return only root categories (no parent)")] = False,
) -> CategoryListResponse:
    """
    List all categories for the current tenant.
    
    - **parent_id**: Optional - Filter by parent category to get children
    - **roots_only**: Optional - If true, return only top-level categories
    
    Categories are ordered hierarchically (parents first, then by name).
    
    Requires: Authentication
    """
    return await category_service.list_categories(current_user, parent_id, roots_only)


@router.get("/stats/product-distribution", response_model=CategoryProductPercentageResponse)
async def get_product_distribution_by_category(
    current_user: Annotated[User, Depends(get_current_user)],
    category_service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryProductPercentageResponse:
    """
    Get the percentage of products distributed across categories.
    
    Returns product counts and percentages for each category,
    including uncategorized products.
    
    Requires: Authentication
    """
    return await category_service.get_product_distribution_by_category(current_user)


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    category_service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryResponse:
    """
    Get a specific category by ID.
    
    - **category_id**: The ID of the category to retrieve
    
    Requires: Authentication
    """
    return await category_service.get_category_by_id(category_id, current_user)


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    data: CategoryUpdateRequest,
    current_user: Annotated[User, Depends(get_current_admin_user)],
    category_service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryResponse:
    """
    Update an existing category (Admin only).
    
    - **category_id**: The ID of the category to update
    - **name**: Optional - New category name
    - **parent_id**: Optional - New parent category ID
    
    Note: Category cannot be its own parent. Only provided fields will be updated.
    
    Requires: Admin role
    """
    return await category_service.update_category(category_id, data, current_user)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    current_user: Annotated[User, Depends(get_current_admin_user)],
    category_service: Annotated[CategoryService, Depends(get_category_service)],
):
    """
    Delete a category (Admin only).
    
    - **category_id**: The ID of the category to delete
    
    Note: Cannot delete categories that have child categories. Delete or reassign children first.
    
    Requires: Admin role
    """
    await category_service.delete_category(category_id, current_user)
