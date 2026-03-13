"""
Product endpoints - CRUD operations for products.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status, Query

from models.models import User
from schemas.product_schema import (
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductListRequest,
    ProductResponse,
    ProductListResponse,
)
from core.dependencies import get_product_service, get_current_user, get_current_admin_user
from services.product_service import ProductService

# ─── Configuration ───────────────────────────────────────────────────────────

router = APIRouter(prefix="/api/products", tags=["Products"])


# ─── Endpoints ───────────────────────────────────────────────────────────────


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreateRequest,
    current_user: Annotated[User, Depends(get_current_admin_user)],
    product_service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    """
    Create a new product (Admin only).
    
    - **sku**: Unique SKU code for the product
    - **name**: Product name
    - **description**: Optional product description
    - **category_id**: Optional category ID
    - **reorder_point**: Minimum stock level for low-stock alerts (default: 0)
    
    Requires: Admin role
    """
    return await product_service.create_product(data, current_user)


@router.get("/", response_model=ProductListResponse)
async def list_products(
    current_user: Annotated[User, Depends(get_current_user)],
    product_service: Annotated[ProductService, Depends(get_product_service)],
    category_id: Annotated[int | None, Query(description="Filter by category ID")] = None,
    search: Annotated[str | None, Query(description="Search by name or SKU")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum number of results")] = 50,
    offset: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
) -> ProductListResponse:
    """
    List all products for the current tenant with optional filters.
    
    - **category_id**: Optional - Filter by category
    - **search**: Optional - Search by product name or SKU (case-insensitive)
    - **limit**: Maximum number of products to return (1-100, default: 50)
    - **offset**: Number of products to skip for pagination (default: 0)
    
    Requires: Authentication
    """
    filters = ProductListRequest(
        category_id=category_id,
        search=search,
        limit=limit,
        offset=offset,
    )
    return await product_service.list_products(filters, current_user)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    product_service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    """
    Get a specific product by ID.
    
    - **product_id**: The ID of the product to retrieve
    
    Requires: Authentication
    """
    return await product_service.get_product_by_id(product_id, current_user)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    data: ProductUpdateRequest,
    current_user: Annotated[User, Depends(get_current_admin_user)],
    product_service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    """
    Update an existing product (Admin only).
    
    - **product_id**: The ID of the product to update
    - **name**: Optional - New product name
    - **description**: Optional - New product description
    - **category_id**: Optional - New category ID
    - **reorder_point**: Optional - New minimum stock level
    
    Note: SKU cannot be updated. Only provided fields will be updated.
    
    Requires: Admin role
    """
    return await product_service.update_product(product_id, data, current_user)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    current_user: Annotated[User, Depends(get_current_admin_user)],
    product_service: Annotated[ProductService, Depends(get_product_service)],
):
    """
    Delete a product (Admin only).
    
    - **product_id**: The ID of the product to delete
    
    Warning: This will cascade delete related stock records and transactions.
    
    Requires: Admin role
    """
    await product_service.delete_product(product_id, current_user)
