"""
Operation Schemas - Request and response models for operation-first stock workflows.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from models.models import OperationStatus, OperationType, TransactionStatus, TransactionType


class OperationItemCreateRequest(BaseModel):
    """A single transaction line in an operation."""

    product_id: int = Field(..., description="Product ID")
    type: TransactionType = Field(..., description="Line movement type: In or Out")
    warehouse_id: int = Field(..., description="Warehouse impacted by this line")
    quantity: int = Field(..., gt=0, description="Quantity for this product line")


class OperationCreateRequest(BaseModel):
    """Request schema for creating a new inventory operation."""

    operation_type: OperationType = Field(..., description="Operation type")
    source_warehouse_id: int | None = Field(
        None,
        description="Source warehouse ID (Sale/Transfer and Out Adjustment)",
    )
    destination_warehouse_id: int | None = Field(
        None,
        description="Destination warehouse ID (Purchase/Return/Transfer and In Adjustment)",
    )
    reference_code: str | None = Field(None, description="Business reference code")
    note: str | None = Field(None, description="Optional operation note")
    status: OperationStatus = Field(
        OperationStatus.PENDING,
        description="Initial operation status",
    )
    items: list[OperationItemCreateRequest] = Field(
        ...,
        min_length=1,
        description="One or more product lines for this operation",
    )


class OperationStatusUpdateRequest(BaseModel):
    """Request schema for status transitions."""

    status: OperationStatus = Field(..., description="New operation status")


class OperationTransactionCompleteRequest(BaseModel):
    """Request schema for completing a transaction line within an operation."""

    received_quantity: int | None = Field(
        None,
        gt=0,
        description="Required for IN transactions to confirm actual received quantity",
    )


class OperationItemResponse(BaseModel):
    id: int
    operation_id: int
    product_id: int
    product_name: str
    product_sku: str
    type: TransactionType
    warehouse_id: int | None
    warehouse_name: str | None
    quantity: int
    movement_status: TransactionStatus


class OperationResponse(BaseModel):
    id: int
    tenant_id: int
    operation_type: OperationType
    status: OperationStatus
    source_warehouse_id: int | None
    source_warehouse_name: str | None
    destination_warehouse_id: int | None
    destination_warehouse_name: str | None
    user_id: int | None
    user_name: str | None
    reference_code: str | None
    note: str | None
    created_at: datetime
    updated_at: datetime
    items: list[OperationItemResponse]


class OperationListResponse(BaseModel):
    operations: list[OperationResponse]
    total: int
    limit: int
    offset: int
