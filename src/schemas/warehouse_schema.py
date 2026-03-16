"""
Warehouse Schemas — Request and Response models for warehouse operations.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from models.models import Warehouse


class WarehouseCreateRequest(BaseModel):
    """Request schema for creating a new warehouse."""
    name: str = Field(..., min_length=1, max_length=100, description="Warehouse name")
    location: str | None = Field(None, description="Warehouse location")


class WarehouseUpdateRequest(BaseModel):
    """Request schema for updating an existing warehouse."""
    name: str | None = Field(None, min_length=1, max_length=100, description="Warehouse name")
    location: str | None = Field(None, description="Warehouse location")


class WarehouseResponse(BaseModel):
    """Response schema for basic warehouse data."""
    id: int
    tenant_id: int
    name: str
    location: str | None

    @classmethod
    def from_warehouse(cls, warehouse: Warehouse) -> WarehouseResponse:
        return cls(
            id=warehouse.id,
            tenant_id=warehouse.tenant_id,
            name=warehouse.name,
            location=warehouse.location,
        )


class ProductStockInfo(BaseModel):
    """Product information with stock quantity in a specific warehouse."""
    product_id: int
    sku: str
    product_name: str
    category_name: str | None
    quantity: int


class WarehouseDetailResponse(BaseModel):
    """Detailed warehouse response with stock information."""
    id: int
    tenant_id: int
    name: str
    location: str | None
    total_unique_products: int
    total_stock: int
    products: list[ProductStockInfo]


class WarehouseSummaryResponse(BaseModel):
    """Summary warehouse response for list view."""
    id: int
    tenant_id: int
    name: str
    location: str | None
    total_unique_products: int
    total_stock: int


class WarehouseListResponse(BaseModel):
    """Response schema for list of warehouses."""
    warehouses: list[WarehouseSummaryResponse]
    total: int
