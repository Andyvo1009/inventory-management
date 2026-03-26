"""
Operation endpoints - Primary write API for inventory workflows.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from core.dependencies import get_current_user, get_operation_service
from models.models import OperationStatus, OperationType, User
from schemas.operation_schema import (
    OperationCreateRequest,
    OperationListResponse,
    OperationResponse,
    OperationStatusUpdateRequest,
    OperationTransactionCompleteRequest,
)
from services.operation_service import OperationService

router = APIRouter(prefix="/api/operations", tags=["Operations"])


@router.post("/", response_model=OperationResponse, status_code=status.HTTP_201_CREATED)
async def create_operation(
    data: OperationCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    operation_service: Annotated[OperationService, Depends(get_operation_service)],
) -> OperationResponse:
    """Create a new operation in deferred mode (no stock change until completion)."""
    return await operation_service.create_operation(data, current_user)


@router.post("/{operation_id}/complete", response_model=OperationResponse)
async def complete_operation(
    operation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    operation_service: Annotated[OperationService, Depends(get_operation_service)],
) -> OperationResponse:
    """Complete an operation and atomically apply stock + transaction ledger updates."""
    return await operation_service.complete_operation(operation_id, current_user)


@router.patch("/{operation_id}/status", response_model=OperationResponse)
async def update_operation_status(
    operation_id: int,
    data: OperationStatusUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    operation_service: Annotated[OperationService, Depends(get_operation_service)],
) -> OperationResponse:
    """Set operation status. If status is Completed, stock and ledger are applied."""
    if data.status == OperationStatus.COMPLETED:
        return await operation_service.complete_operation(operation_id, current_user)

    return await operation_service.update_operation_status(
        operation_id=operation_id,
        new_status=data.status,
        current_user=current_user,
    )


@router.get("/", response_model=OperationListResponse)
async def list_operations(
    current_user: Annotated[User, Depends(get_current_user)],
    operation_service: Annotated[OperationService, Depends(get_operation_service)],
    operation_type: Annotated[OperationType | None, Query(description="Filter by operation type")] = None,
    op_status: Annotated[OperationStatus | None, Query(alias="status", description="Filter by operation status")] = None,
    warehouse_id: Annotated[int | None, Query(description="Filter by warehouse (source or destination)")] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> OperationListResponse:
    """List tenant operations with optional filters."""
    return await operation_service.list_operations(
        current_user=current_user,
        operation_type=operation_type,
        op_status=op_status,
        warehouse_id=warehouse_id,
        limit=limit,
        offset=offset,
    )


@router.get("/{operation_id}", response_model=OperationResponse)
async def get_operation(
    operation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    operation_service: Annotated[OperationService, Depends(get_operation_service)],
) -> OperationResponse:
    """Get a single operation with item lines."""
    return await operation_service.get_operation_by_id(operation_id, current_user)


@router.post("/{operation_id}/transactions/{transaction_id}/complete", response_model=OperationResponse)
async def complete_transaction(
    operation_id: int,
    transaction_id: int,
    data: OperationTransactionCompleteRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    operation_service: Annotated[OperationService, Depends(get_operation_service)],
) -> OperationResponse:
    """
    Complete a single transaction within an operation.
    Applies stock effects and updates transaction status.
    If all transactions are complete, operation is marked COMPLETED.
    """
    return await operation_service.complete_transaction(
        operation_id,
        transaction_id,
        current_user,
        received_quantity=data.received_quantity,
    )


@router.post("/{operation_id}/transactions/{transaction_id}/fail", response_model=OperationResponse)
async def fail_transaction(
    operation_id: int,
    transaction_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    operation_service: Annotated[OperationService, Depends(get_operation_service)],
) -> OperationResponse:
    """
    Mark a transaction as failed.
    This cascades failure to the entire operation and all its other transactions.
    """
    return await operation_service.fail_transaction(operation_id, transaction_id, current_user)
