"""
Operation Service - operation-first business logic with deferred stock execution.
"""

from __future__ import annotations

import asyncpg
from fastapi import HTTPException, status

from models.models import OperationStatus, TransactionStatus, OperationType, TransactionType, User, InventoryTransaction
from repositories.operation_repository import OperationRepository
from repositories.product_repository import ProductRepository
from repositories.stock_repository import StockRepository
from repositories.transaction_repository import TransactionRepository
from repositories.warehouse_repository import WarehouseRepository
from schemas.operation_schema import (
    OperationCreateRequest,
    OperationListResponse,
    OperationResponse,
)


class OperationService:
    def __init__(self, conn: asyncpg.Connection):
        self._conn = conn
        self._operation_repo = OperationRepository(conn)
        self._product_repo = ProductRepository(conn)
        self._warehouse_repo = WarehouseRepository(conn)
        self._stock_repo = StockRepository(conn)
        self._transaction_repo = TransactionRepository(conn)

    async def create_operation(
        self,
        data: OperationCreateRequest,
        current_user: User,
    ) -> OperationResponse:
        await self._validate_operation_request(data, current_user.tenant_id)

        warehouse_names: dict[int, str] = {}
        for warehouse_id in {item.warehouse_id for item in data.items if item.warehouse_id}:
            warehouse = await self._warehouse_repo.get_by_id(
                warehouse_id=warehouse_id,
                tenant_id=current_user.tenant_id,
            )
            warehouse_names[warehouse_id] = warehouse.name if warehouse else f"Warehouse {warehouse_id}"

        source_name = (
            warehouse_names.get(data.source_warehouse_id)
            if data.source_warehouse_id
            else None
        )
        destination_name = (
            warehouse_names.get(data.destination_warehouse_id)
            if data.destination_warehouse_id
            else None
        )

        async with self._conn.transaction():
            operation = await self._operation_repo.create(
                tenant_id=current_user.tenant_id,
                operation_type=data.operation_type,
                status=data.status,
                source_warehouse_id=data.source_warehouse_id,
                destination_warehouse_id=data.destination_warehouse_id,
                reference_code=data.reference_code,
                user_id=current_user.id,
                note=data.note,
                conn=self._conn,
            )

            for item in data.items:
                item_warehouse_name = warehouse_names.get(item.warehouse_id)
                transaction_note = self._compose_transaction_note(
                    operation_type=data.operation_type,
                    transaction_type=item.type,
                    item_warehouse_name=item_warehouse_name,
                    source_name=source_name,
                    destination_name=destination_name,
                    user_note=data.note,
                )
                await self._transaction_repo.record(
                    tenant_id=current_user.tenant_id,
                    operation_id=operation.id,
                    product_id=item.product_id,
                    warehouse_id=item.warehouse_id,
                    type=item.type,
                    quantity=item.quantity,
                    user_id=current_user.id,
                    note=transaction_note,
                    conn=self._conn,
                )

            if data.status in {OperationStatus.DRAFT, OperationStatus.PENDING, OperationStatus.IN_TRANSIT}:
                tx_status = (
                    TransactionStatus.PENDING
                    if data.status in {OperationStatus.PENDING, OperationStatus.IN_TRANSIT}
                    else TransactionStatus.DRAFT
                )
                await self._transaction_repo.update_movement_status_by_operation(
                    operation_id=operation.id,
                    tenant_id=current_user.tenant_id,
                    movement_status=tx_status,
                    conn=self._conn,
                )

        detailed = await self._operation_repo.get_detailed(
            operation_id=operation.id,
            tenant_id=current_user.tenant_id,
        )
        return OperationResponse(**detailed)

    async def complete_operation(
        self,
        operation_id: int,
        current_user: User,
    ) -> OperationResponse:
        """
        Complete an operation by processing all its transactions.
        - Completes each transaction by applying stock effects
        - If all transactions complete, operation is marked COMPLETED
        - If any transaction fails, operation and all transactions are marked FAILED
        - For TRANSFER operations, when OUT transaction completes, operation moves to IN_TRANSIT
        """
        operation = None

        try:
            async with self._conn.transaction():
                operation = await self._operation_repo.get_by_id_for_update(
                    operation_id=operation_id,
                    tenant_id=current_user.tenant_id,
                    conn=self._conn,
                )
                if not operation:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Operation with ID {operation_id} not found",
                    )

                if operation.status == OperationStatus.COMPLETED:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Operation is already completed",
                    )

                if operation.status in {OperationStatus.CANCELLED, OperationStatus.FAILED}:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Cannot complete an operation in {operation.status.value} status",
                    )

                items = await self._transaction_repo.list_inventory_by_operation(
                    operation_id=operation.id,
                    tenant_id=current_user.tenant_id,
                    conn=self._conn,
                )
                if not items:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Operation has no items",
                    )

                # Process each transaction individually
                await self._process_operation_transactions(
                    operation=operation,
                    items=items,
                    current_user=current_user,
                )

                # Check if all transactions completed successfully
                all_completed = await self._transaction_repo.check_all_transactions_completed(
                    operation_id=operation.id,
                    tenant_id=current_user.tenant_id,
                    conn=self._conn,
                )

                if all_completed:
                    # All transactions completed, mark operation as completed
                    await self._operation_repo.update_status(
                        operation_id=operation.id,
                        tenant_id=current_user.tenant_id,
                        status=OperationStatus.COMPLETED,
                        conn=self._conn,
                    )
                else:
                    # Some transactions still pending/draft, don't change status
                    # (operation stays in current status for user to continue completing)
                    pass

        except ValueError as exc:
            if operation is not None:
                print(f"Error completing operation {operation.id}: {exc}", flush=True)
                async with self._conn.transaction():
                    # Mark operation as failed
                    await self._set_operation_failure_status(
                        operation_id=operation.id,
                        tenant_id=current_user.tenant_id,
                        conn=self._conn,
                    )
                    # Mark non-completed transactions as failed; completed ones stay immutable.
                    await self._fail_non_completed_transactions_by_operation(
                        operation_id=operation.id,
                        tenant_id=current_user.tenant_id,
                        conn=self._conn,
                    )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            )

        detailed = await self._operation_repo.get_detailed(
            operation_id=operation_id,
            tenant_id=current_user.tenant_id,
        )
        return OperationResponse(**detailed)

    async def list_operations(
        self,
        current_user: User,
        operation_type: OperationType | None,
        op_status: OperationStatus | None,
        warehouse_id: int | None,
        limit: int,
        offset: int,
    ) -> OperationListResponse:
        operations = await self._operation_repo.list_by_tenant(
            tenant_id=current_user.tenant_id,
            operation_type=operation_type,
            status=op_status,
            warehouse_id=warehouse_id,
            limit=limit,
            offset=offset,
        )

        detailed = []
        for op in operations:
            full = await self._operation_repo.get_detailed(op["id"], current_user.tenant_id)
            if full:
                detailed.append(OperationResponse(**full))

        return OperationListResponse(
            operations=detailed,
            total=len(detailed),
            limit=limit,
            offset=offset,
        )

    async def get_operation_by_id(
        self,
        operation_id: int,
        current_user: User,
    ) -> OperationResponse:
        operation = await self._operation_repo.get_detailed(
            operation_id=operation_id,
            tenant_id=current_user.tenant_id,
        )
        if not operation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Operation with ID {operation_id} not found",
            )
        return OperationResponse(**operation)

    async def update_operation_status(
        self,
        operation_id: int,
        new_status: OperationStatus,
        current_user: User,
    ) -> OperationResponse:
        if new_status == OperationStatus.COMPLETED:
            return await self.complete_operation(operation_id, current_user)

        operation = await self._operation_repo.get_by_id(
            operation_id=operation_id,
            tenant_id=current_user.tenant_id,
        )
        if not operation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Operation with ID {operation_id} not found",
            )

        if operation.status == OperationStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Completed operations cannot change status",
            )

        updated = await self._operation_repo.update_status(
            operation_id=operation_id,
            tenant_id=current_user.tenant_id,
            status=new_status,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Operation with ID {operation_id} not found",
            )
        detailed = await self._operation_repo.get_detailed(updated.id, current_user.tenant_id)
        return OperationResponse(**detailed)

    async def _validate_operation_request(self, data: OperationCreateRequest, tenant_id: int) -> None:
        await self._validate_warehouse(data.source_warehouse_id, tenant_id, "source")
        await self._validate_warehouse(data.destination_warehouse_id, tenant_id, "destination")

        for item in data.items:
            product = await self._product_repo.get_by_id(item.product_id, tenant_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {item.product_id} not found",
                )

            await self._validate_warehouse(item.warehouse_id, tenant_id, "item")

            if item.type not in {TransactionType.IN, TransactionType.OUT}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Operation line item type must be In or Out",
                )

    async def _validate_warehouse(
        self,
        warehouse_id: int | None,
        tenant_id: int,
        label: str,
    ) -> None:
        if not warehouse_id:
            return
        warehouse = await self._warehouse_repo.get_by_id(warehouse_id=warehouse_id, tenant_id=tenant_id)
        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{label.capitalize()} warehouse with ID {warehouse_id} not found",
            )

    async def complete_transaction(
        self,
        operation_id: int,
        transaction_id: int,
        current_user: User,
        received_quantity: int | None = None,
    ) -> OperationResponse:
        """
        Complete a single transaction within an operation.
        - Applies stock effects for the transaction
        - Marks transaction as COMPLETED
        - Checks if all transactions are now completed; if so, marks operation as COMPLETED
        - If transaction fails, marks both transaction and operation as FAILED
        
        Returns: Updated operation details
        """
        try:
            async with self._conn.transaction():
                # Get the transaction
                transaction = await self._transaction_repo.get_by_id(transaction_id, current_user.tenant_id)
                if not transaction:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Transaction with ID {transaction_id} not found",
                    )

                # Verify it belongs to the target operation
                if transaction.operation_id != operation_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Transaction {transaction_id} does not belong to operation {operation_id}",
                    )

                # Check if already completed
                if transaction.movement_status == TransactionStatus.COMPLETED:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Transaction {transaction_id} is already completed",
                    )

                if transaction.movement_status == TransactionStatus.FAILED:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Transaction {transaction_id} has already failed",
                    )

                # Get operation
                operation = await self._operation_repo.get_by_id_for_update(
                    operation_id=operation_id,
                    tenant_id=current_user.tenant_id,
                    conn=self._conn,
                )
                if not operation:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Operation with ID {operation_id} not found",
                    )

                if operation.status == OperationStatus.COMPLETED:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Operation is already completed",
                    )

                if operation.status in {OperationStatus.CANCELLED, OperationStatus.FAILED}:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Cannot complete a transaction in an operation with {operation.status.value} status",
                    )

                # In transfer operations, inbound completion is only allowed after all OUT lines are resolved.
                if operation.operation_type == OperationType.TRANSFER and transaction.type == TransactionType.IN:
                    operation_items = await self._transaction_repo.list_inventory_by_operation(
                        operation_id=operation_id,
                        tenant_id=current_user.tenant_id,
                        conn=self._conn,
                    )
                    self._ensure_transfer_out_resolved_before_in(operation_items)
                    effective_in_qty = received_quantity if received_quantity is not None else transaction.quantity
                    self._validate_transfer_in_quantity(transaction, operation_items, effective_in_qty)

                # Apply stock effect
                try:
                    if transaction.type == TransactionType.IN:
                        if received_quantity is None:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="received_quantity is required when completing IN transactions",
                            )
                        if received_quantity > transaction.quantity:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=(
                                    f"Received quantity cannot exceed planned quantity: expected up to "
                                    f"{transaction.quantity}, got {received_quantity}."
                                ),
                            )

                        if received_quantity < transaction.quantity:
                            partial_note = (
                                f"Partial receipt confirmed: expected {transaction.quantity}, "
                                f"received {received_quantity}"
                            )
                            merged_note = (
                                f"{transaction.note} | {partial_note}"
                                if transaction.note
                                else partial_note
                            )
                            updated_tx = await self._transaction_repo.update_transaction_quantity_and_note(
                                transaction_id=transaction_id,
                                tenant_id=current_user.tenant_id,
                                quantity=received_quantity,
                                note=merged_note,
                                conn=self._conn,
                            )
                            if updated_tx:
                                transaction = updated_tx

                        await self._stock_repo.increment(
                            product_id=transaction.product_id,
                            warehouse_id=transaction.warehouse_id,
                            qty=transaction.quantity,
                            tenant_id=current_user.tenant_id,
                            conn=self._conn,
                        )
                    elif transaction.type == TransactionType.OUT:
                        await self._stock_repo.decrement(
                            product_id=transaction.product_id,
                            warehouse_id=transaction.warehouse_id,
                            qty=transaction.quantity,
                            tenant_id=current_user.tenant_id,
                            conn=self._conn,
                        )
                    else:
                        raise ValueError("Unsupported transaction type")

                    # Mark transaction as completed
                    await self._transaction_repo.update_transaction_status(
                        transaction_id=transaction_id,
                        tenant_id=current_user.tenant_id,
                        movement_status=TransactionStatus.COMPLETED,
                        conn=self._conn,
                    )

                    # Check if all transactions are now completed
                    all_completed = await self._transaction_repo.check_all_transactions_completed(
                        operation_id=operation_id,
                        tenant_id=current_user.tenant_id,
                        conn=self._conn,
                    )

                    if all_completed:
                        await self._operation_repo.update_status(
                            operation_id=operation_id,
                            tenant_id=current_user.tenant_id,
                            status=OperationStatus.COMPLETED,
                            conn=self._conn,
                        )
                    else:
                        # Check if this is a TRANSFER operation and this was an OUT transaction
                        if operation.operation_type == OperationType.TRANSFER and transaction.type == TransactionType.OUT:
                            out_transactions = await self._transaction_repo.get_transactions_by_type(
                                operation_id=operation_id,
                                tenant_id=current_user.tenant_id,
                                transaction_type=TransactionType.OUT,
                                conn=self._conn,
                            )
                            # Check if all OUT transactions are completed
                            all_out_completed = all(
                                tx.movement_status == TransactionStatus.COMPLETED for tx in out_transactions
                            )
                            if all_out_completed and operation.status != OperationStatus.IN_TRANSIT:
                                await self._operation_repo.update_status(
                                    operation_id=operation_id,
                                    tenant_id=current_user.tenant_id,
                                    status=OperationStatus.IN_TRANSIT,
                                    conn=self._conn,
                                )

                except Exception as exc:
                    # Mark transaction as failed
                    await self._transaction_repo.update_transaction_status(
                        transaction_id=transaction_id,
                        tenant_id=current_user.tenant_id,
                        movement_status=TransactionStatus.FAILED,
                        conn=self._conn,
                    )
                    raise ValueError(f"Failed to apply stock effect: {str(exc)}")

        except ValueError as exc:
            # Mark operation and all transactions as failed
            async with self._conn.transaction():
                await self._set_operation_failure_status(
                    operation_id=operation_id,
                    tenant_id=current_user.tenant_id,
                    conn=self._conn,
                )
                await self._fail_non_completed_transactions_by_operation(
                    operation_id=operation_id,
                    tenant_id=current_user.tenant_id,
                    conn=self._conn,
                )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            )

        detailed = await self._operation_repo.get_detailed(
            operation_id=operation_id,
            tenant_id=current_user.tenant_id,
        )
        return OperationResponse(**detailed)

    async def fail_transaction(
        self,
        operation_id: int,
        transaction_id: int,
        current_user: User,
    ) -> OperationResponse:
        """
        Mark a transaction as failed, which cascades failure to the entire operation.
        - Marks transaction as FAILED
        - Marks operation as FAILED
        - Marks all other transactions as FAILED
        
        Returns: Updated operation details
        """
        try:
            async with self._conn.transaction():
                # Get the transaction
                transaction = await self._transaction_repo.get_by_id(transaction_id, current_user.tenant_id)
                if not transaction:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Transaction with ID {transaction_id} not found",
                    )

                # Verify it belongs to the target operation
                if transaction.operation_id != operation_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Transaction {transaction_id} does not belong to operation {operation_id}",
                    )

                # Check if already in a terminal state
                if transaction.movement_status in {TransactionStatus.COMPLETED, TransactionStatus.FAILED}:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Cannot fail a transaction that is already in {transaction.movement_status.value} state",
                    )
                # Mark this transaction as failed
                await self._transaction_repo.update_transaction_status(
                    transaction_id=transaction_id,
                    tenant_id=current_user.tenant_id,
                    movement_status=TransactionStatus.FAILED,
                    conn=self._conn,
                )
                # Mark operation as failed
                await self._set_operation_failure_status(
                    operation_id=operation_id,
                    tenant_id=current_user.tenant_id,
                    conn=self._conn,
                )
                print(f"Transaction {transaction_id} marked as failed, operation {operation_id} marked as failed", flush=True)
                # Mark non-completed transactions as failed; completed ones stay immutable.
                await self._fail_non_completed_transactions_by_operation(
                    operation_id=operation_id,
                    tenant_id=current_user.tenant_id,
                    conn=self._conn,
                )

        except HTTPException:
            raise
        except Exception as exc:
            print(exc, flush=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to mark transaction as failed: {str(exc)}",
            )

        detailed = await self._operation_repo.get_detailed(
            operation_id=operation_id,
            tenant_id=current_user.tenant_id,
        )
        return OperationResponse(**detailed)

    async def _set_operation_failure_status(
        self,
        operation_id: int,
        tenant_id: int,
        conn: asyncpg.Connection | None = None,
    ):
        """
        Mark operation as failed with backward compatibility.

        Some existing databases do not include 'Failed' in operation_status enum;
        for those, fallback to 'Cancelled' to avoid 500s.
        """
        c = conn or self._conn
        try:
            return await self._operation_repo.update_status(
                operation_id=operation_id,
                tenant_id=tenant_id,
                status=OperationStatus.CANCELLED,
                conn=c,
            )
        except asyncpg.exceptions.UndefinedObjectError:
            print(
                f"OperationStatus.FAILED not defined in database, falling back to CANCELLED for operation {operation_id}",
                flush=True,
            )
            return await self._operation_repo.update_status(
                operation_id=operation_id,
                tenant_id=tenant_id,
                status=OperationStatus.CANCELLED,
                conn=c,
            )

    def _compose_transaction_note(
        self,
        operation_type: OperationType,
        transaction_type: TransactionType,
        item_warehouse_name: str | None,
        source_name: str | None,
        destination_name: str | None,
        user_note: str | None,
    ) -> str:
        if operation_type == OperationType.TRANSFER:
            from_name = source_name or "Unknown source"
            to_name = destination_name or "Unknown destination"
            if transaction_type == TransactionType.OUT:
                base = f"Transfer operation - dispatch from {from_name} to {to_name}"
            else:
                base = f"Transfer operation - receive at {to_name} from {from_name}"
        else:
            warehouse_part = f" at {item_warehouse_name}" if item_warehouse_name else ""
            base = f"{operation_type.value} operation - {transaction_type.value}{warehouse_part}"

        if user_note:
            return f"{base} | {user_note}"
        return base

    async def _process_operation_transactions(
        self,
        operation,
        items: list[InventoryTransaction],
        current_user: User,
    ) -> None:
        """
        Process each transaction in an operation:
        1. Apply stock effects (increment/decrement)
        2. Mark transaction as COMPLETED
        3. For TRANSFER operations, when OUT completes, set operation to IN_TRANSIT
        4. If any transaction fails, cascade failure to entire operation
        """
        out_transactions_completed = False

        if operation.operation_type == OperationType.TRANSFER:
            items = sorted(items, key=lambda tx: 0 if tx.type == TransactionType.OUT else 1)

        for item in items:
            if item.movement_status == TransactionStatus.COMPLETED:
                # Completed transactions are immutable and must not be reapplied.
                continue

            if item.movement_status == TransactionStatus.FAILED:
                raise ValueError(f"Transaction {item.id} is already failed")

            try:
                # Apply stock effect based on transaction type
                if item.type == TransactionType.IN:
                    if operation.operation_type == OperationType.TRANSFER:
                        self._ensure_transfer_out_resolved_before_in(items)
                        self._validate_transfer_in_quantity(item, items)
                    await self._stock_repo.increment(
                        product_id=item.product_id,
                        warehouse_id=item.warehouse_id,
                        qty=item.quantity,
                        tenant_id=current_user.tenant_id,
                        conn=self._conn,
                    )
                elif item.type == TransactionType.OUT:
                    await self._stock_repo.decrement(
                        product_id=item.product_id,
                        warehouse_id=item.warehouse_id,
                        qty=item.quantity,
                        tenant_id=current_user.tenant_id,
                        conn=self._conn,
                    )
                    out_transactions_completed = True
                else:
                    raise ValueError("Unsupported transaction line type. Use In or Out.")

                # Mark transaction as COMPLETED after successful stock effect
                await self._transaction_repo.update_transaction_status(
                    transaction_id=item.id,
                    tenant_id=current_user.tenant_id,
                    movement_status=TransactionStatus.COMPLETED,
                    conn=self._conn,
                )

            except Exception as exc:
                if item.movement_status != TransactionStatus.COMPLETED:
                    await self._transaction_repo.update_transaction_status(
                        transaction_id=item.id,
                        tenant_id=current_user.tenant_id,
                        movement_status=TransactionStatus.FAILED,
                        conn=self._conn,
                    )
                # Propagate error to cascade failure to entire operation
                raise ValueError(f"Transaction {item.id} failed: {str(exc)}")

        # For TRANSFER operations, when OUT transaction completes, set operation to IN_TRANSIT
        if operation.operation_type == OperationType.TRANSFER and out_transactions_completed:
            out_transactions = await self._transaction_repo.get_transactions_by_type(
                operation_id=operation.id,
                tenant_id=current_user.tenant_id,
                transaction_type=TransactionType.OUT,
                conn=self._conn,
            )
            # Check if all OUT transactions are completed
            all_out_completed = all(
                tx.movement_status == TransactionStatus.COMPLETED for tx in out_transactions
            )
            if all_out_completed:
                await self._operation_repo.update_status(
                    operation_id=operation.id,
                    tenant_id=current_user.tenant_id,
                    status=OperationStatus.IN_TRANSIT,
                    conn=self._conn,
                )

    async def _fail_non_completed_transactions_by_operation(
        self,
        operation_id: int,
        tenant_id: int,
        conn: asyncpg.Connection | None = None,
    ) -> None:
        c = conn or self._conn
        items = await self._transaction_repo.list_inventory_by_operation(
            operation_id=operation_id,
            tenant_id=tenant_id,
            conn=c,
        )
        for item in items:
            if item.movement_status == TransactionStatus.COMPLETED:
                continue
            if item.movement_status == TransactionStatus.FAILED:
                continue
            await self._transaction_repo.update_transaction_status(
                transaction_id=item.id,
                tenant_id=tenant_id,
                movement_status=TransactionStatus.FAILED,
                conn=c,
            )

    def _ensure_transfer_out_resolved_before_in(
        self,
        items: list[InventoryTransaction],
    ) -> None:
        out_items = [item for item in items if item.type == TransactionType.OUT]
        unresolved_out = [
            item for item in out_items if item.movement_status in {TransactionStatus.DRAFT, TransactionStatus.PENDING}
        ]
        if unresolved_out:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Transfer OUT transactions must be completed or failed before processing IN transactions",
            )

        failed_out = [item for item in out_items if item.movement_status == TransactionStatus.FAILED]
        if failed_out:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot process transfer IN transactions because one or more OUT transactions failed",
            )

    def _validate_transfer_in_quantity(
        self,
        in_transaction: InventoryTransaction,
        items: list[InventoryTransaction],
        requested_in_quantity: int | None = None,
    ) -> None:
        completed_out_qty = sum(
            item.quantity
            for item in items
            if item.type == TransactionType.OUT
            and item.product_id == in_transaction.product_id
            and item.movement_status == TransactionStatus.COMPLETED
        )
        completed_in_qty_before_current = sum(
            item.quantity
            for item in items
            if item.type == TransactionType.IN
            and item.product_id == in_transaction.product_id
            and item.id != in_transaction.id
            and item.movement_status == TransactionStatus.COMPLETED
        )

        in_qty = requested_in_quantity if requested_in_quantity is not None else in_transaction.quantity
        available_to_receive = completed_out_qty - completed_in_qty_before_current
        if in_qty > available_to_receive:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Inbound quantity mismatch for product {in_transaction.product_id}: "
                    f"can receive up to {max(available_to_receive, 0)}, "
                    f"but transaction requires {in_qty}"
                ),
            )

