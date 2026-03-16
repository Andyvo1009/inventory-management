"""
Transaction endpoints - Stock movement operations.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status, Query

from models.models import User, TransactionType
from schemas.transaction_schema import (
    TransactionCreateRequest,
    TransactionListRequest,
    TransactionResponse,
    TransactionListResponse,
)
from core.dependencies import get_transaction_service, get_current_user
from services.transaction_service import TransactionService

# ─── Configuration ───────────────────────────────────────────────────────────

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


# ─── Endpoints ───────────────────────────────────────────────────────────────


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: TransactionCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    transaction_service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> TransactionResponse:
    """
    Create a new inventory transaction (stock movement).
    
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
    - **notes**: Optional notes about the transaction
    
    Requires: Authentication
    """
    return await transaction_service.create_transaction(data, current_user)


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
    - Transaction type, quantity, notes, and timestamp
    
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
