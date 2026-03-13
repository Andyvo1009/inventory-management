"""
Category Schemas — Request and Response models for category operations.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from models.models import Category


class CategoryCreateRequest(BaseModel):
    """Request schema for creating a new category."""
    name: str = Field(..., min_length=1, max_length=255, description="Category name")
    parent_id: int | None = Field(None, description="Parent category ID for hierarchical structure")


class CategoryUpdateRequest(BaseModel):
    """Request schema for updating a category."""
    name: str | None = Field(None, min_length=1, max_length=255, description="Category name")
    parent_id: int | None = Field(None, description="Parent category ID")


class CategoryResponse(BaseModel):
    """Response schema for category data."""
    id: int
    tenant_id: int
    name: str
    parent_id: int | None

    @classmethod
    def from_category(cls, category: Category) -> CategoryResponse:
        return cls(
            id=category.id,
            tenant_id=category.tenant_id,
            name=category.name,
            parent_id=category.parent_id,
        )


class CategoryListResponse(BaseModel):
    """Response schema for list of categories."""
    categories: list[CategoryResponse]
    total: int


class CategoryProductPercentage(BaseModel):
    """Product distribution data for a single category."""
    category_id: int | None = Field(None, description="Category ID (None for uncategorized products)")
    category_name: str = Field(..., description="Category name")
    product_count: int = Field(..., description="Number of products in this category")
    percentage: float = Field(..., description="Percentage of total products (0-100)")


class CategoryProductPercentageResponse(BaseModel):
    """Response schema for product distribution by category."""
    distribution: list[CategoryProductPercentage]
    total_products: int = Field(..., description="Total number of products across all categories")
