"""
Transaction Service - Business logic for transaction operations.
"""

from __future__ import annotations

import asyncpg
from fastapi import HTTPException, status

from models.models import User, TransactionType
from repositories.interfaces import (
    ITransactionRepository,
    IProductRepository,
    IWarehouseRepository,
    IStockRepository,
)
from repositories.transaction_repository import TransactionRepository
from repositories.product_repository import ProductRepository
from repositories.warehouse_repository import WarehouseRepository
from repositories.stock_repository import StockRepository
from schemas.transaction_schema import (
    TransactionCreateRequest,
    TransactionListRequest,
    TransactionResponse,
    TransactionListResponse,
)


class TransactionService:
    """Service class for transaction operations."""

    def __init__(
        self,
        conn: asyncpg.Connection,
        transaction_repo: ITransactionRepository = None,
        product_repo: IProductRepository = None,
        warehouse_repo: IWarehouseRepository = None,
        stock_repo: IStockRepository = None,
    ):
        self._conn = conn
        self._transaction_repo = transaction_repo or TransactionRepository(conn)
        self._product_repo = product_repo or ProductRepository(conn)
        self._warehouse_repo = warehouse_repo or WarehouseRepository(conn)
        self._stock_repo = stock_repo or StockRepository(conn)

    async def create_transaction(
        self, data: TransactionCreateRequest, current_user: User
    ) -> TransactionResponse:
        """Direct transaction writes are deprecated in favor of operation workflows."""
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Direct transaction creation is deprecated. Use /api/operations instead.",
        )

    async def get_transaction_by_id(
        self, transaction_id: int, current_user: User
    ) -> TransactionResponse:
        """
        Get a transaction by ID with full details.
        
        Args:
            transaction_id: Transaction ID
            current_user: The authenticated user
            
        Returns:
            TransactionResponse with transaction information
            
        Raises:
            HTTPException: If transaction not found
        """
        transaction = await self._transaction_repo.get_by_id_detailed(
            tx_id=transaction_id, tenant_id=current_user.tenant_id
        )

        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction with ID {transaction_id} not found",
            )

        return transaction

    async def list_transactions(
        self, filters: TransactionListRequest, current_user: User
    ) -> TransactionListResponse:
        """
        List transactions with optional filters.
        
        Args:
            filters: Filtering and pagination parameters
            current_user: The authenticated user
            
        Returns:
            TransactionListResponse with list of transactions
        """
        transactions = await self._transaction_repo.list_by_tenant(
            tenant_id=current_user.tenant_id,
            type=filters.type,
            warehouse_id=filters.warehouse_id,
            product_id=filters.product_id,
            limit=filters.limit,
            offset=filters.offset,
        )

        return TransactionListResponse(
            transactions=transactions,
            total=len(transactions),
            limit=filters.limit,
            offset=filters.offset,
        )

    async def list_transactions_by_operation(
        self,
        operation_id: int,
        current_user: User,
    ) -> TransactionListResponse:
        transactions = await self._transaction_repo.list_by_operation(
            operation_id=operation_id,
            tenant_id=current_user.tenant_id,
        )
        return TransactionListResponse(
            transactions=transactions,
            total=len(transactions),
            limit=len(transactions),
            offset=0,
        )
