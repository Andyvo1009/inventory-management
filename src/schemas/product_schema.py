"""
Product Schemas — Request and Response models for product operations.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from models.models import Product


class ProductCreateRequest(BaseModel):
    """Request schema for creating a new product."""
    sku: str = Field(..., min_length=1, max_length=100, description="Unique SKU code")
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: str | None = Field(None, description="Product description")
    category_id: int | None = Field(None, description="Category ID")
    reorder_point: int = Field(0, ge=0, description="Minimum stock level for alerts")


class ProductUpdateRequest(BaseModel):
    """Request schema for updating an existing product."""
    name: str | None = Field(None, min_length=1, max_length=255, description="Product name")
    description: str | None = Field(None, description="Product description")
    category_id: int | None = Field(None, description="Category ID")
    reorder_point: int | None = Field(None, ge=0, description="Minimum stock level for alerts")


class ProductListRequest(BaseModel):
    """Request schema for filtering product list."""
    category_id: int | None = Field(None, description="Filter by category ID")
    search: str | None = Field(None, description="Search by name or SKU")
    limit: int = Field(50, ge=1, le=100, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of records to skip")


class ProductResponse(BaseModel):
    """Response schema for product data."""
    id: int
    tenant_id: int
    category_id: int | None
    sku: str
    name: str
    description: str | None
    reorder_point: int
    category_name: str | None = None

    @classmethod
    def from_product(cls, product: Product, category_name: str | None = None) -> ProductResponse:
        return cls(
            id=product.id,
            tenant_id=product.tenant_id,
            category_id=product.category_id,
            sku=product.sku,
            name=product.name,
            description=product.description,
            reorder_point=product.reorder_point,
            category_name=category_name,
        )


class ProductListResponse(BaseModel):
    """Response schema for list of products."""
    products: list[ProductResponse]
    total: int
    limit: int
    offset: int
