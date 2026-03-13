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
        """
        Create a new inventory transaction (stock movement).
        
        Args:
            data: Transaction creation request data
            current_user: The authenticated user
            
        Returns:
            TransactionResponse with created transaction information
            
        Raises:
            HTTPException: If validation fails or insufficient stock
        """
        # Validate product exists and belongs to tenant
        product_check = await self._conn.fetchrow(
            "SELECT id FROM products WHERE id = $1 AND tenant_id = $2",
            data.product_id,
            current_user.tenant_id,
        )
        if not product_check:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {data.product_id} not found",
            )

        # Validate warehouses and transaction type logic
        if data.type == TransactionType.IN:
            if not data.des_warehouse_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="des_warehouse_id is required for IN transactions",
                )
            # Verify destination warehouse exists
            dest_wh = await self._warehouse_repo.get_by_id(
                warehouse_id=data.des_warehouse_id,
                tenant_id=current_user.tenant_id,
            )
            if not dest_wh:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Destination warehouse with ID {data.des_warehouse_id} not found",
                )

        elif data.type == TransactionType.OUT:
            if not data.origin_warehouse_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="origin_warehouse_id is required for OUT transactions",
                )
            # Verify origin warehouse exists
            origin_wh = await self._warehouse_repo.get_by_id(
                warehouse_id=data.origin_warehouse_id,
                tenant_id=current_user.tenant_id,
            )
            if not origin_wh:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Origin warehouse with ID {data.origin_warehouse_id} not found",
                )

        elif data.type == TransactionType.TRANSFER:
            if not data.origin_warehouse_id or not data.des_warehouse_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Both origin_warehouse_id and des_warehouse_id are required for TRANSFER transactions",
                )
            if data.origin_warehouse_id == data.des_warehouse_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Origin and destination warehouses must be different for transfers",
                )
            # Verify both warehouses exist
            origin_wh = await self._warehouse_repo.get_by_id(
                warehouse_id=data.origin_warehouse_id,
                tenant_id=current_user.tenant_id,
            )
            dest_wh = await self._warehouse_repo.get_by_id(
                warehouse_id=data.des_warehouse_id,
                tenant_id=current_user.tenant_id,
            )
            if not origin_wh:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Origin warehouse with ID {data.origin_warehouse_id} not found",
                )
            if not dest_wh:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Destination warehouse with ID {data.des_warehouse_id} not found",
                )

        # Use transaction to ensure atomicity
        try:
            async with self._conn.transaction():
                # Update stock levels based on transaction type
                
                if data.type == TransactionType.IN:
                    await self._stock_repo.increment(
                        product_id=data.product_id,
                        warehouse_id=data.des_warehouse_id,
                        qty=data.quantity,
                        conn=self._conn,
                    )
                elif data.type == TransactionType.OUT:
                    await self._stock_repo.decrement(
                        product_id=data.product_id,
                        warehouse_id=data.origin_warehouse_id,
                        qty=data.quantity,
                        conn=self._conn,
                    )
                elif data.type == TransactionType.TRANSFER:
                    await self._stock_repo.decrement(
                        product_id=data.product_id,
                        warehouse_id=data.origin_warehouse_id,
                        qty=data.quantity,
                        conn=self._conn,
                    )
                    await self._stock_repo.increment(
                        product_id=data.product_id,
                        warehouse_id=data.des_warehouse_id,
                        qty=data.quantity,
                        conn=self._conn,
                    )
            

                # Record the transaction
                await self._transaction_repo.record(
                    tenant_id=current_user.tenant_id,
                    product_id=data.product_id,
                    type=data.type,
                    quantity=data.quantity,
                    origin_warehouse_id=data.origin_warehouse_id,
                    des_warehouse_id=data.des_warehouse_id,
                    user_id=current_user.id,
                    notes=data.notes,
                    conn=self._conn,
                )

        except ValueError as e:
            # Catch insufficient stock errors from decrement
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

        # Fetch and return the detailed transaction
        transaction = await self._conn.fetchrow(
            """
            SELECT 
                t.id, 
                t.tenant_id, 
                t.type, 
                t.product_id,
                p.name AS product_name,
                p.sku AS product_sku,
                t.quantity,
                t.origin_warehouse_id,
                ow.name AS origin_warehouse_name,
                t.des_warehouse_id,
                dw.name AS des_warehouse_name,
                t.user_id,
                u.name AS user_name,
                t.notes,
                t.timestamp
            FROM inventory_transactions t
            JOIN products p ON t.product_id = p.id
            LEFT JOIN warehouses ow ON t.origin_warehouse_id = ow.id
            LEFT JOIN warehouses dw ON t.des_warehouse_id = dw.id
            LEFT JOIN users u ON t.user_id = u.id
            WHERE t.tenant_id = $1 AND t.product_id = $2 AND t.user_id = $3
            ORDER BY t.timestamp DESC
            LIMIT 1
            """,
            current_user.tenant_id,
            data.product_id,
            current_user.id,
        )

        return TransactionResponse(**transaction)

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
