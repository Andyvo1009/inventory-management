"""
Transaction Schemas — Request and Response models for transaction operations.
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field

from models.models import TransactionType


class TransactionCreateRequest(BaseModel):
    """Deprecated compatibility schema for creating transactions via operations."""
    product_id: int = Field(..., description="Product ID")
    type: TransactionType = Field(..., description="Transaction type: In, Out, or Transfer")
    quantity: int = Field(..., gt=0, description="Quantity to move (must be positive)")
    origin_warehouse_id: int | None = Field(None, description="Source warehouse ID (required for Out and Transfer)")
    des_warehouse_id: int | None = Field(None, description="Destination warehouse ID (required for In and Transfer)")
    note: str | None = Field(None, description="Optional note about the transaction")


class TransactionListRequest(BaseModel):
    """Request schema for filtering transaction list."""
    type: TransactionType | None = Field(None, description="Filter by transaction type")
    warehouse_id: int | None = Field(None, description="Filter by warehouse (origin or destination)")
    product_id: int | None = Field(None, description="Filter by product")
    limit: int = Field(100, ge=1, le=500, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of records to skip")


class TransactionResponse(BaseModel):
    """Response schema for transaction data with joined information."""
    id: int
    tenant_id: int
    type: TransactionType
    product_id: int
    product_name: str
    product_sku: str
    operation_id: int
    quantity: int
    origin_warehouse_id: int | None
    origin_warehouse_name: str | None
    des_warehouse_id: int | None
    des_warehouse_name: str | None
    user_id: int | None
    user_name: str | None
    note: str | None
    timestamp: datetime
    movement_status: str


class TransactionListResponse(BaseModel):
    """Response schema for list of transactions."""
    transactions: list[TransactionResponse]
    total: int
    limit: int
    offset: int
