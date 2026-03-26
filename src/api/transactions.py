"""
Transaction endpoints - Stock movement operations.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from models.models import OperationType, User, TransactionType
from schemas.operation_schema import OperationCreateRequest, OperationItemCreateRequest
from schemas.transaction_schema import (
    TransactionCreateRequest,
    TransactionListRequest,
    TransactionResponse,
    TransactionListResponse,
)
from core.dependencies import get_current_user, get_operation_service, get_transaction_service
from services.operation_service import OperationService
from services.transaction_service import TransactionService

# ─── Configuration ───────────────────────────────────────────────────────────

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


# ─── Endpoints ───────────────────────────────────────────────────────────────


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: TransactionCreateRequest,
    response: Response,
    current_user: Annotated[User, Depends(get_current_user)],
    operation_service: Annotated[OperationService, Depends(get_operation_service)],
    transaction_service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> TransactionResponse:
    """
    Deprecated: create a transaction via an operation compatibility adapter.
    
    Transaction types and requirements:
    - **IN**: Requires des_warehouse_id (receiving stock)
    - **OUT**: Requires origin_warehouse_id (removing stock)
    - **TRANSFER**: Requires both origin_warehouse_id and des_warehouse_id (moving between warehouses)
    
    Fields:
    - **product_id**: The product being moved
    - **type**: Transaction type (In, Out, Transfer)
    - **quantity**: Quantity to move (must be positive)
    - **origin_warehouse_id**: Source warehouse (for OUT and TRANSFER)
    - **des_warehouse_id**: Destination warehouse (for IN and TRANSFER)
    - **note**: Optional note about the transaction
    
    Requires: Authentication
    """
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "Wed, 30 Sep 2026 23:59:59 GMT"

    if data.type == TransactionType.IN:
        operation_type = OperationType.PURCHASE
        items = [
            OperationItemCreateRequest(
                product_id=data.product_id,
                type=TransactionType.IN,
                warehouse_id=data.des_warehouse_id,
                quantity=data.quantity,
            )
        ]
    elif data.type == TransactionType.OUT:
        operation_type = OperationType.SALE
        items = [
            OperationItemCreateRequest(
                product_id=data.product_id,
                type=TransactionType.OUT,
                warehouse_id=data.origin_warehouse_id,
                quantity=data.quantity,
            )
        ]
    else:
        operation_type = OperationType.TRANSFER
        items = [
            OperationItemCreateRequest(
                product_id=data.product_id,
                type=TransactionType.OUT,
                warehouse_id=data.origin_warehouse_id,
                quantity=data.quantity,
            ),
            OperationItemCreateRequest(
                product_id=data.product_id,
                type=TransactionType.IN,
                warehouse_id=data.des_warehouse_id,
                quantity=data.quantity,
            ),
        ]

    operation = await operation_service.create_operation(
        OperationCreateRequest(
            operation_type=operation_type,
            source_warehouse_id=data.origin_warehouse_id,
            destination_warehouse_id=data.des_warehouse_id,
            reference_code="legacy-transaction-adapter",
            note=data.note,
            items=items,
        ),
        current_user,
    )

    await operation_service.complete_operation(operation.id, current_user=current_user)

    transactions = await transaction_service.list_transactions_by_operation(
        operation_id=operation.id,
        current_user=current_user,
    )
    if not transactions.transactions:
        raise RuntimeError("Operation completed but no transaction entries were found")
    return transactions.transactions[0]


@router.get("/", response_model=TransactionListResponse)
async def list_transactions(
    current_user: Annotated[User, Depends(get_current_user)],
    transaction_service: Annotated[TransactionService, Depends(get_transaction_service)],
    type: Annotated[TransactionType | None, Query(description="Filter by transaction type")] = None,
    warehouse_id: Annotated[int | None, Query(description="Filter by warehouse (origin or destination)")] = None,
    product_id: Annotated[int | None, Query(description="Filter by product ID")] = None,
    limit: Annotated[int, Query(ge=1, le=500, description="Maximum number of results")] = 100,
    offset: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
) -> TransactionListResponse:
    """
    List all inventory transactions for the current tenant.
    
    Returns transactions with full details:
    - Product name and SKU
    - Warehouse names (origin and/or destination)
    - User who created the transaction
    - Transaction type, quantity, note, and timestamp
    
    Filters:
    - **type**: Filter by transaction type (In, Out, Transfer)
    - **warehouse_id**: Filter by warehouse (matches either origin or destination)
    - **product_id**: Filter by product
    - **limit**: Maximum number of transactions to return (1-500, default: 100)
    - **offset**: Number of transactions to skip for pagination (default: 0)
    
    Requires: Authentication
    """
    filters = TransactionListRequest(
        type=type,
        warehouse_id=warehouse_id,
        product_id=product_id,
        limit=limit,
        offset=offset,
    )
    return await transaction_service.list_transactions(filters, current_user)


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    transaction_service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> TransactionResponse:
    """
    Get a specific transaction by ID with full details.
    
    - **transaction_id**: The ID of the transaction to retrieve
    
    Requires: Authentication
    """
    return await transaction_service.get_transaction_by_id(transaction_id, current_user)
