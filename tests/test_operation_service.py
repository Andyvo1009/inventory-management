"""
Unit tests for OperationService.

OperationService implements the operation-first inventory workflow: every stock
movement is initiated through an InventoryOperation (Purchase, Sale, Transfer,
Adjustment, Return) and fulfilled by completing the individual transaction lines
that belong to it.

Coverage map
─────────────────────────────────────────────────────────────────────────────
create_operation
  • PURCHASE with one IN item succeeds and returns OperationResponse  (1)
  • SALE with one OUT item succeeds                                   (1)
  • PENDING status syncs transaction movement_status to PENDING       (1)
  • DRAFT status syncs transaction movement_status to DRAFT           (1)
  • COMPLETED initial status skips movement_status sync              (1)
  • Unknown product raises HTTP 404                                   (1)
  • Unknown item warehouse raises HTTP 404                            (1)
  • Item type TRANSFER raises HTTP 400                                (1)

complete_operation
  • All IN items complete → operation marked COMPLETED               (1)
  • Already COMPLETED operation raises HTTP 409                       (1)
  • CANCELLED operation raises HTTP 409                               (1)
  • FAILED operation raises HTTP 409                                  (1)
  • Operation not found raises HTTP 404                               (1)
  • Operation with no items raises HTTP 400                           (1)
  • Stock error cancels operation and fails pending movements         (1) ← original

get_operation_by_id
  • Found → returns OperationResponse                                 (1)
  • Not found → raises HTTP 404                                       (1)

list_operations
  • Returns populated OperationListResponse                          (1)
  • Empty tenant → returns empty list, total=0                       (1)

update_operation_status
  • Non-COMPLETED status update succeeds                              (1)
  • COMPLETED target delegates to complete_operation                  (1)
  • Operation not found raises HTTP 404                               (1)
  • Already-COMPLETED operation raises HTTP 409                       (1)

complete_transaction
  • IN transaction with full receipt succeeds                         (1)
  • OUT transaction succeeds                                          (1)
  • Transaction not found raises HTTP 404                             (1)
  • Transaction belongs to different operation raises HTTP 400        (1)
  • Already COMPLETED transaction raises HTTP 409                     (1)
  • Already FAILED transaction raises HTTP 409                        (1)
  • Operation already COMPLETED raises HTTP 409                       (1)
  • Operation CANCELLED raises HTTP 409                               (1)
  • IN without received_quantity raises HTTP 400                      (1)
  • received_quantity > planned raises HTTP 400                       (1)
  • Partial receipt updates quantity and increments stock by new qty  (1)
  • Stock error marks tx FAILED and cascades to operation             (1)
  • TRANSFER IN blocked before OUT resolved raises HTTP 409           (1)
  • TRANSFER OUT completion transitions operation to IN_TRANSIT       (1)
  • Final transaction completes → operation marked COMPLETED          (1)

fail_transaction
  • Success: tx → FAILED, op → CANCELLED, siblings → FAILED          (1)
  • Transaction not found raises HTTP 404                             (1)
  • Transaction belongs to different operation raises HTTP 400        (1)
  • COMPLETED transaction cannot be failed → HTTP 409                (1)
  • FAILED transaction cannot be failed again → HTTP 409             (1)

_compose_transaction_note (sync, unit)
  • TRANSFER OUT note mentions dispatch direction                     (1)
  • TRANSFER IN note mentions receive direction                       (1)
  • Non-TRANSFER includes operation type and warehouse name           (1)
  • User note is appended after a pipe separator                      (1)
  • No warehouse name → note still has no warehouse part             (1)

_ensure_transfer_out_resolved_before_in (sync, unit)
  • PENDING OUT raises HTTP 409                                       (1)
  • DRAFT OUT raises HTTP 409                                         (1)
  • FAILED OUT raises HTTP 409                                        (1)
  • All OUT COMPLETED → no exception                                  (1)

_validate_transfer_in_quantity (sync, unit)
  • in_qty > available raises HTTP 400                                (1)
  • in_qty == available passes                                        (1)
  • in_qty < available passes                                         (1)
─────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from models.models import (
    InventoryOperation,
    InventoryTransaction,
    OperationStatus,
    OperationType,
    TransactionStatus,
    TransactionType,
    Warehouse,
)
from schemas.operation_schema import (
    OperationCreateRequest,
    OperationItemCreateRequest,
)
from services.operation_service import OperationService


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _make_service(
    mock_conn,
    operation_repo=None,
    transaction_repo=None,
    stock_repo=None,
    product_repo=None,
    warehouse_repo=None,
) -> OperationService:
    """Build an OperationService with all five repos replaced by AsyncMocks."""
    svc = OperationService(mock_conn)
    svc._operation_repo = operation_repo or AsyncMock()
    svc._transaction_repo = transaction_repo or AsyncMock()
    svc._stock_repo = stock_repo or AsyncMock()
    svc._product_repo = product_repo or AsyncMock()
    svc._warehouse_repo = warehouse_repo or AsyncMock()
    return svc


def _make_operation(
    op_id: int = 1,
    op_type: OperationType = OperationType.PURCHASE,
    status: OperationStatus = OperationStatus.PENDING,
    source_id: int | None = None,
    dest_id: int | None = 1,
) -> InventoryOperation:
    """Create a minimal InventoryOperation dataclass."""
    return InventoryOperation(
        id=op_id,
        tenant_id=1,
        user_id=1,
        operation_type=op_type,
        status=status,
        source_warehouse_id=source_id,
        destination_warehouse_id=dest_id,
        reference_code=None,
        note=None,
        created_at=datetime(2026, 3, 1),
        updated_at=datetime(2026, 3, 1),
    )


def _make_tx(
    tx_id: int = 1,
    op_id: int = 1,
    tx_type: TransactionType = TransactionType.IN,
    status: TransactionStatus = TransactionStatus.PENDING,
    qty: int = 10,
    product_id: int = 1,
    warehouse_id: int = 1,
) -> InventoryTransaction:
    """Create a minimal InventoryTransaction dataclass."""
    return InventoryTransaction(
        id=tx_id,
        tenant_id=1,
        operation_id=op_id,
        product_id=product_id,
        user_id=1,
        warehouse_id=warehouse_id,
        type=tx_type,
        quantity=qty,
        note=None,
        timestamp=datetime(2026, 3, 1),
        movement_status=status,
    )


def _make_detailed(
    op_id: int = 1,
    op_type: OperationType = OperationType.PURCHASE,
    status: OperationStatus = OperationStatus.COMPLETED,
    items: list | None = None,
) -> dict:
    """
    Build a dict matching OperationResponse field names, as returned by
    OperationRepository.get_detailed.
    """
    return {
        "id": op_id,
        "tenant_id": 1,
        "operation_type": op_type,
        "status": status,
        "source_warehouse_id": None,
        "source_warehouse_name": None,
        "destination_warehouse_id": None,
        "destination_warehouse_name": None,
        "user_id": 1,
        "user_name": "Admin User",
        "reference_code": None,
        "note": None,
        "created_at": datetime(2026, 3, 1),
        "updated_at": datetime(2026, 3, 1),
        "items": items or [],
    }


def _single_item_request(
    tx_type: TransactionType = TransactionType.IN,
    warehouse_id: int = 1,
    product_id: int = 1,
    quantity: int = 10,
) -> OperationCreateRequest:
    """Build an OperationCreateRequest with a single line item."""
    op_type = (
        OperationType.PURCHASE if tx_type == TransactionType.IN else OperationType.SALE
    )
    return OperationCreateRequest(
        operation_type=op_type,
        items=[
            OperationItemCreateRequest(
                product_id=product_id,
                type=tx_type,
                warehouse_id=warehouse_id,
                quantity=quantity,
            )
        ],
    )


# ─── create_operation ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_operation_purchase_success(
    mock_conn, admin_user, sample_product, sample_warehouse
):
    """
    create_operation with a PURCHASE type and one IN item:
    - validates the product and item warehouse
    - persists the operation and one transaction line
    - syncs movement_status to PENDING (default initial status)
    - returns the full OperationResponse from get_detailed
    """
    product_repo = AsyncMock()
    product_repo.get_by_id.return_value = sample_product

    warehouse_repo = AsyncMock()
    warehouse_repo.get_by_id.return_value = sample_warehouse

    operation_repo = AsyncMock()
    operation_repo.create.return_value = _make_operation(status=OperationStatus.PENDING)
    operation_repo.get_detailed.return_value = _make_detailed(
        status=OperationStatus.PENDING
    )

    transaction_repo = AsyncMock()

    svc = _make_service(
        mock_conn,
        operation_repo=operation_repo,
        transaction_repo=transaction_repo,
        product_repo=product_repo,
        warehouse_repo=warehouse_repo,
    )

    result = await svc.create_operation(_single_item_request(), admin_user)

    assert result.id == 1
    assert result.operation_type == OperationType.PURCHASE
    assert result.status == OperationStatus.PENDING
    operation_repo.create.assert_awaited_once()
    transaction_repo.record.assert_awaited_once()
    transaction_repo.update_movement_status_by_operation.assert_awaited_once_with(
        operation_id=1,
        tenant_id=admin_user.tenant_id,
        movement_status=TransactionStatus.PENDING,
        conn=mock_conn,
    )


@pytest.mark.asyncio
async def test_create_operation_sale_success(
    mock_conn, admin_user, sample_product, sample_warehouse
):
    """
    create_operation with a SALE type and one OUT item succeeds and returns a
    response whose operation_type is SALE.
    """
    product_repo = AsyncMock()
    product_repo.get_by_id.return_value = sample_product
    warehouse_repo = AsyncMock()
    warehouse_repo.get_by_id.return_value = sample_warehouse
    operation_repo = AsyncMock()
    operation_repo.create.return_value = _make_operation(
        op_type=OperationType.SALE, status=OperationStatus.PENDING
    )
    operation_repo.get_detailed.return_value = _make_detailed(
        op_type=OperationType.SALE, status=OperationStatus.PENDING
    )
    transaction_repo = AsyncMock()

    svc = _make_service(
        mock_conn,
        operation_repo=operation_repo,
        transaction_repo=transaction_repo,
        product_repo=product_repo,
        warehouse_repo=warehouse_repo,
    )
    data = OperationCreateRequest(
        operation_type=OperationType.SALE,
        items=[
            OperationItemCreateRequest(
                product_id=1, type=TransactionType.OUT, warehouse_id=1, quantity=5
            )
        ],
    )

    result = await svc.create_operation(data, admin_user)

    assert result.operation_type == OperationType.SALE
    transaction_repo.record.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_operation_pending_status_sets_pending_tx_status(
    mock_conn, admin_user, sample_product, sample_warehouse
):
    """
    When the operation is created with PENDING status (the default), all
    transaction lines must have their movement_status set to PENDING via
    update_movement_status_by_operation.
    """
    product_repo = AsyncMock()
    product_repo.get_by_id.return_value = sample_product
    warehouse_repo = AsyncMock()
    warehouse_repo.get_by_id.return_value = sample_warehouse
    operation_repo = AsyncMock()
    operation_repo.create.return_value = _make_operation(status=OperationStatus.PENDING)
    operation_repo.get_detailed.return_value = _make_detailed(
        status=OperationStatus.PENDING
    )
    transaction_repo = AsyncMock()

    svc = _make_service(
        mock_conn,
        operation_repo=operation_repo,
        transaction_repo=transaction_repo,
        product_repo=product_repo,
        warehouse_repo=warehouse_repo,
    )
    data = OperationCreateRequest(
        operation_type=OperationType.PURCHASE,
        status=OperationStatus.PENDING,
        items=[
            OperationItemCreateRequest(
                product_id=1, type=TransactionType.IN, warehouse_id=1, quantity=10
            )
        ],
    )

    await svc.create_operation(data, admin_user)

    transaction_repo.update_movement_status_by_operation.assert_awaited_once_with(
        operation_id=1,
        tenant_id=1,
        movement_status=TransactionStatus.PENDING,
        conn=mock_conn,
    )


@pytest.mark.asyncio
async def test_create_operation_draft_status_sets_draft_tx_status(
    mock_conn, admin_user, sample_product, sample_warehouse
):
    """
    When the operation is created with DRAFT status, all transaction lines
    must have their movement_status set to DRAFT via
    update_movement_status_by_operation.
    """
    product_repo = AsyncMock()
    product_repo.get_by_id.return_value = sample_product
    warehouse_repo = AsyncMock()
    warehouse_repo.get_by_id.return_value = sample_warehouse
    operation_repo = AsyncMock()
    operation_repo.create.return_value = _make_operation(status=OperationStatus.DRAFT)
    operation_repo.get_detailed.return_value = _make_detailed(
        status=OperationStatus.DRAFT
    )
    transaction_repo = AsyncMock()

    svc = _make_service(
        mock_conn,
        operation_repo=operation_repo,
        transaction_repo=transaction_repo,
        product_repo=product_repo,
        warehouse_repo=warehouse_repo,
    )
    data = OperationCreateRequest(
        operation_type=OperationType.PURCHASE,
        status=OperationStatus.DRAFT,
        items=[
            OperationItemCreateRequest(
                product_id=1, type=TransactionType.IN, warehouse_id=1, quantity=10
            )
        ],
    )

    await svc.create_operation(data, admin_user)

    transaction_repo.update_movement_status_by_operation.assert_awaited_once_with(
        operation_id=1,
        tenant_id=1,
        movement_status=TransactionStatus.DRAFT,
        conn=mock_conn,
    )


@pytest.mark.asyncio
async def test_create_operation_completed_status_skips_tx_status_update(
    mock_conn, admin_user, sample_product, sample_warehouse
):
    """
    When the operation is initially set to COMPLETED status, the service must
    NOT call update_movement_status_by_operation, because COMPLETED is not
    in the {DRAFT, PENDING, IN_TRANSIT} set that triggers that call.
    """
    product_repo = AsyncMock()
    product_repo.get_by_id.return_value = sample_product
    warehouse_repo = AsyncMock()
    warehouse_repo.get_by_id.return_value = sample_warehouse
    operation_repo = AsyncMock()
    operation_repo.create.return_value = _make_operation(
        status=OperationStatus.COMPLETED
    )
    operation_repo.get_detailed.return_value = _make_detailed(
        status=OperationStatus.COMPLETED
    )
    transaction_repo = AsyncMock()

    svc = _make_service(
        mock_conn,
        operation_repo=operation_repo,
        transaction_repo=transaction_repo,
        product_repo=product_repo,
        warehouse_repo=warehouse_repo,
    )
    data = OperationCreateRequest(
        operation_type=OperationType.PURCHASE,
        status=OperationStatus.COMPLETED,
        items=[
            OperationItemCreateRequest(
                product_id=1, type=TransactionType.IN, warehouse_id=1, quantity=10
            )
        ],
    )

    await svc.create_operation(data, admin_user)

    transaction_repo.update_movement_status_by_operation.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_operation_product_not_found_raises_404(mock_conn, admin_user):
    """
    create_operation raises HTTP 404 when a requested product does not exist
    in the caller's tenant.  Validation happens before the DB transaction
    opens, so no operation row is written.
    """
    product_repo = AsyncMock()
    product_repo.get_by_id.return_value = None  # product missing

    operation_repo = AsyncMock()
    svc = _make_service(
        mock_conn, operation_repo=operation_repo, product_repo=product_repo
    )

    with pytest.raises(HTTPException) as exc:
        await svc.create_operation(_single_item_request(), admin_user)

    assert exc.value.status_code == 404
    assert "Product" in exc.value.detail
    operation_repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_operation_warehouse_not_found_raises_404(
    mock_conn, admin_user, sample_product
):
    """
    create_operation raises HTTP 404 when the item's warehouse does not exist
    in the caller's tenant.
    """
    product_repo = AsyncMock()
    product_repo.get_by_id.return_value = sample_product

    warehouse_repo = AsyncMock()
    warehouse_repo.get_by_id.return_value = None  # warehouse missing

    operation_repo = AsyncMock()
    svc = _make_service(
        mock_conn,
        operation_repo=operation_repo,
        product_repo=product_repo,
        warehouse_repo=warehouse_repo,
    )

    with pytest.raises(HTTPException) as exc:
        await svc.create_operation(_single_item_request(), admin_user)

    assert exc.value.status_code == 404
    operation_repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_operation_item_type_transfer_raises_400(
    mock_conn, admin_user, sample_product, sample_warehouse
):
    """
    An operation line item with type=TRANSFER is invalid; only IN and OUT are
    accepted.  The service must raise HTTP 400 with an informative message.
    """
    product_repo = AsyncMock()
    product_repo.get_by_id.return_value = sample_product
    warehouse_repo = AsyncMock()
    warehouse_repo.get_by_id.return_value = sample_warehouse

    svc = _make_service(
        mock_conn, product_repo=product_repo, warehouse_repo=warehouse_repo
    )
    data = OperationCreateRequest(
        operation_type=OperationType.TRANSFER,
        items=[
            OperationItemCreateRequest(
                product_id=1,
                type=TransactionType.TRANSFER,  # invalid for line items
                warehouse_id=1,
                quantity=5,
            )
        ],
    )

    with pytest.raises(HTTPException) as exc:
        await svc.create_operation(data, admin_user)

    assert exc.value.status_code == 400
    assert "In or Out" in exc.value.detail


# ─── complete_operation ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_complete_operation_success(mock_conn, admin_user):
    """
    complete_operation with a single PENDING IN item:
    - increments stock for the item's product and warehouse
    - marks the transaction COMPLETED
    - detects all transactions done → marks operation COMPLETED
    - returns the full OperationResponse
    """
    operation_repo = AsyncMock()
    transaction_repo = AsyncMock()
    stock_repo = AsyncMock()

    operation_repo.get_by_id_for_update.return_value = _make_operation(
        status=OperationStatus.PENDING
    )
    transaction_repo.list_inventory_by_operation.return_value = [
        _make_tx(tx_type=TransactionType.IN, status=TransactionStatus.PENDING)
    ]
    transaction_repo.check_all_transactions_completed.return_value = True
    operation_repo.get_detailed.return_value = _make_detailed(
        status=OperationStatus.COMPLETED
    )

    svc = _make_service(
        mock_conn,
        operation_repo=operation_repo,
        transaction_repo=transaction_repo,
        stock_repo=stock_repo,
    )
    result = await svc.complete_operation(1, admin_user)

    assert result.status == OperationStatus.COMPLETED
    stock_repo.increment.assert_awaited_once()
    transaction_repo.update_transaction_status.assert_awaited_once_with(
        transaction_id=1,
        tenant_id=admin_user.tenant_id,
        movement_status=TransactionStatus.COMPLETED,
        conn=mock_conn,
    )
    operation_repo.update_status.assert_awaited_once_with(
        operation_id=1,
        tenant_id=admin_user.tenant_id,
        status=OperationStatus.COMPLETED,
        conn=mock_conn,
    )


@pytest.mark.asyncio
async def test_complete_operation_already_completed_raises_409(mock_conn, admin_user):
    """
    complete_operation raises HTTP 409 when the operation is already COMPLETED,
    preventing idempotent re-application of stock mutations.
    """
    operation_repo = AsyncMock()
    operation_repo.get_by_id_for_update.return_value = _make_operation(
        status=OperationStatus.COMPLETED
    )

    svc = _make_service(mock_conn, operation_repo=operation_repo)

    with pytest.raises(HTTPException) as exc:
        await svc.complete_operation(1, admin_user)

    assert exc.value.status_code == 409
    assert "already completed" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_complete_operation_cancelled_raises_409(mock_conn, admin_user):
    """
    complete_operation raises HTTP 409 when the operation is CANCELLED.
    Cancelled operations are terminal and cannot be completed.
    """
    operation_repo = AsyncMock()
    operation_repo.get_by_id_for_update.return_value = _make_operation(
        status=OperationStatus.CANCELLED
    )

    svc = _make_service(mock_conn, operation_repo=operation_repo)

    with pytest.raises(HTTPException) as exc:
        await svc.complete_operation(1, admin_user)

    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_complete_operation_failed_raises_409(mock_conn, admin_user):
    """
    complete_operation raises HTTP 409 when the operation is already FAILED.
    FAILED is a terminal status; re-completing would corrupt stock levels.
    """
    operation_repo = AsyncMock()
    operation_repo.get_by_id_for_update.return_value = _make_operation(
        status=OperationStatus.FAILED
    )

    svc = _make_service(mock_conn, operation_repo=operation_repo)

    with pytest.raises(HTTPException) as exc:
        await svc.complete_operation(1, admin_user)

    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_complete_operation_not_found_raises_404(mock_conn, admin_user):
    """
    complete_operation raises HTTP 404 when the operation does not exist in
    the caller's tenant.
    """
    operation_repo = AsyncMock()
    operation_repo.get_by_id_for_update.return_value = None

    svc = _make_service(mock_conn, operation_repo=operation_repo)

    with pytest.raises(HTTPException) as exc:
        await svc.complete_operation(999, admin_user)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_complete_operation_no_items_raises_400(mock_conn, admin_user):
    """
    complete_operation raises HTTP 400 when the operation has no transaction
    items.  An operation without items is considered misconfigured.
    """
    operation_repo = AsyncMock()
    transaction_repo = AsyncMock()

    operation_repo.get_by_id_for_update.return_value = _make_operation(
        status=OperationStatus.PENDING
    )
    transaction_repo.list_inventory_by_operation.return_value = []  # no items

    svc = _make_service(
        mock_conn, operation_repo=operation_repo, transaction_repo=transaction_repo
    )

    with pytest.raises(HTTPException) as exc:
        await svc.complete_operation(1, admin_user)

    assert exc.value.status_code == 400
    assert "no items" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_complete_operation_stock_error_cancels_operation_and_fails_movements(
    mock_conn,
    admin_user,
):
    """
    When a stock decrement raises ValueError (e.g. no stock record exists),
    complete_operation must:
      1. Re-raise as HTTP 400
      2. Mark the operation CANCELLED via update_status
      3. Mark all non-completed transactions FAILED via update_transaction_status

    The failure cascade happens inside a fresh DB transaction so partial stock
    effects from earlier lines are rolled back by the outer transaction context.
    """
    service = OperationService(mock_conn)

    operation_repo = AsyncMock()
    transaction_repo = AsyncMock()
    stock_repo = AsyncMock()

    service._operation_repo = operation_repo
    service._transaction_repo = transaction_repo
    service._stock_repo = stock_repo

    operation_repo.get_by_id_for_update.return_value = InventoryOperation(
        id=11,
        tenant_id=admin_user.tenant_id,
        user_id=admin_user.id,
        operation_type=OperationType.ADJUSTMENT,
        status=OperationStatus.PENDING,
        source_warehouse_id=1,
        destination_warehouse_id=None,
        reference_code=None,
        note=None,
        created_at=datetime(2026, 3, 1, 10, 0, 0),
        updated_at=datetime(2026, 3, 1, 10, 0, 0),
    )

    pending_tx = InventoryTransaction(
        id=101,
        tenant_id=admin_user.tenant_id,
        operation_id=11,
        product_id=1,
        user_id=admin_user.id,
        warehouse_id=1,
        type=TransactionType.OUT,
        quantity=5,
        note=None,
        timestamp=datetime(2026, 3, 1, 10, 0, 0),
        movement_status=TransactionStatus.PENDING,
    )
    transaction_repo.list_inventory_by_operation.return_value = [pending_tx]
    stock_repo.decrement.side_effect = ValueError(
        "No stock record found for product in this warehouse."
    )

    with pytest.raises(HTTPException) as exc:
        await service.complete_operation(11, admin_user)

    assert exc.value.status_code == 400

    # Operation must be cancelled
    operation_repo.update_status.assert_awaited_once_with(
        operation_id=11,
        tenant_id=admin_user.tenant_id,
        status=OperationStatus.CANCELLED,
        conn=mock_conn,
    )
    # The pending transaction must be marked FAILED (at least once)
    transaction_repo.update_transaction_status.assert_any_await(
        transaction_id=101,
        tenant_id=admin_user.tenant_id,
        movement_status=TransactionStatus.FAILED,
        conn=mock_conn,
    )


# ─── get_operation_by_id ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_operation_by_id_success(mock_conn, admin_user):
    """
    get_operation_by_id returns the OperationResponse when the operation
    exists in the caller's tenant.
    """
    operation_repo = AsyncMock()
    operation_repo.get_detailed.return_value = _make_detailed(
        op_id=5, status=OperationStatus.PENDING
    )

    svc = _make_service(mock_conn, operation_repo=operation_repo)
    result = await svc.get_operation_by_id(5, admin_user)

    assert result.id == 5
    assert result.status == OperationStatus.PENDING
    operation_repo.get_detailed.assert_awaited_once_with(
        operation_id=5, tenant_id=admin_user.tenant_id
    )


@pytest.mark.asyncio
async def test_get_operation_by_id_not_found_raises_404(mock_conn, admin_user):
    """
    get_operation_by_id raises HTTP 404 when get_detailed returns None,
    meaning no operation with that ID exists in the caller's tenant.
    """
    operation_repo = AsyncMock()
    operation_repo.get_detailed.return_value = None

    svc = _make_service(mock_conn, operation_repo=operation_repo)

    with pytest.raises(HTTPException) as exc:
        await svc.get_operation_by_id(999, admin_user)

    assert exc.value.status_code == 404


# ─── list_operations ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_operations_returns_operations(mock_conn, admin_user):
    """
    list_operations returns an OperationListResponse with one entry for each
    operation returned by list_by_tenant, enriched with get_detailed data.
    total equals the number of operations returned.
    """
    operation_repo = AsyncMock()
    operation_repo.list_by_tenant.return_value = [{"id": 1}, {"id": 2}]
    operation_repo.get_detailed.side_effect = [
        _make_detailed(op_id=1),
        _make_detailed(op_id=2),
    ]

    svc = _make_service(mock_conn, operation_repo=operation_repo)
    result = await svc.list_operations(
        current_user=admin_user,
        operation_type=None,
        op_status=None,
        warehouse_id=None,
        limit=50,
        offset=0,
    )

    assert result.total == 2
    assert len(result.operations) == 2
    assert result.limit == 50
    assert result.offset == 0


@pytest.mark.asyncio
async def test_list_operations_empty(mock_conn, admin_user):
    """
    list_operations returns total=0 and an empty list when the tenant has
    no operations matching the given filters.
    """
    operation_repo = AsyncMock()
    operation_repo.list_by_tenant.return_value = []

    svc = _make_service(mock_conn, operation_repo=operation_repo)
    result = await svc.list_operations(
        current_user=admin_user,
        operation_type=None,
        op_status=None,
        warehouse_id=None,
        limit=50,
        offset=0,
    )

    assert result.total == 0
    assert result.operations == []


# ─── update_operation_status ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_operation_status_to_cancelled(mock_conn, admin_user):
    """
    update_operation_status to CANCELLED:
    - fetches the operation
    - calls update_status with the new status
    - returns the detailed response
    """
    operation_repo = AsyncMock()
    operation_repo.get_by_id.return_value = _make_operation(
        status=OperationStatus.PENDING
    )
    updated_op = _make_operation(status=OperationStatus.CANCELLED)
    operation_repo.update_status.return_value = updated_op
    operation_repo.get_detailed.return_value = _make_detailed(
        status=OperationStatus.CANCELLED
    )

    svc = _make_service(mock_conn, operation_repo=operation_repo)
    result = await svc.update_operation_status(1, OperationStatus.CANCELLED, admin_user)

    assert result.status == OperationStatus.CANCELLED
    operation_repo.update_status.assert_awaited_once_with(
        operation_id=1,
        tenant_id=admin_user.tenant_id,
        status=OperationStatus.CANCELLED,
    )


@pytest.mark.asyncio
async def test_update_operation_status_completed_delegates(mock_conn, admin_user):
    """
    When new_status is COMPLETED, update_operation_status must delegate the
    call to complete_operation rather than calling update_status directly.
    This ensures the same stock-mutation and transaction-completion logic runs.
    """
    operation_repo = AsyncMock()
    transaction_repo = AsyncMock()
    stock_repo = AsyncMock()

    operation_repo.get_by_id_for_update.return_value = _make_operation(
        status=OperationStatus.PENDING
    )
    transaction_repo.list_inventory_by_operation.return_value = [
        _make_tx(tx_type=TransactionType.IN, status=TransactionStatus.PENDING)
    ]
    transaction_repo.check_all_transactions_completed.return_value = True
    operation_repo.get_detailed.return_value = _make_detailed(
        status=OperationStatus.COMPLETED
    )

    svc = _make_service(
        mock_conn,
        operation_repo=operation_repo,
        transaction_repo=transaction_repo,
        stock_repo=stock_repo,
    )
    result = await svc.update_operation_status(1, OperationStatus.COMPLETED, admin_user)

    assert result.status == OperationStatus.COMPLETED
    # complete_operation is used → update_status called with COMPLETED
    operation_repo.update_status.assert_awaited_with(
        operation_id=1,
        tenant_id=admin_user.tenant_id,
        status=OperationStatus.COMPLETED,
        conn=mock_conn,
    )


@pytest.mark.asyncio
async def test_update_operation_status_not_found_raises_404(mock_conn, admin_user):
    """
    update_operation_status raises HTTP 404 when the operation does not
    exist in the caller's tenant.
    """
    operation_repo = AsyncMock()
    operation_repo.get_by_id.return_value = None

    svc = _make_service(mock_conn, operation_repo=operation_repo)

    with pytest.raises(HTTPException) as exc:
        await svc.update_operation_status(999, OperationStatus.CANCELLED, admin_user)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_operation_status_already_completed_raises_409(
    mock_conn, admin_user
):
    """
    update_operation_status raises HTTP 409 when trying to update the status
    of an already-COMPLETED operation.  COMPLETED is immutable.
    """
    operation_repo = AsyncMock()
    operation_repo.get_by_id.return_value = _make_operation(
        status=OperationStatus.COMPLETED
    )

    svc = _make_service(mock_conn, operation_repo=operation_repo)

    with pytest.raises(HTTPException) as exc:
        await svc.update_operation_status(1, OperationStatus.CANCELLED, admin_user)

    assert exc.value.status_code == 409


# ─── complete_transaction ─────────────────────────────────────────────────────


def _setup_complete_transaction(
    mock_conn,
    tx: InventoryTransaction,
    operation: InventoryOperation,
    all_completed: bool = True,
    out_transactions: list[InventoryTransaction] | None = None,
):
    """
    Wire up the minimum set of mocks needed for a successful complete_transaction
    call.  Returns (svc, operation_repo, transaction_repo, stock_repo).
    """
    operation_repo = AsyncMock()
    transaction_repo = AsyncMock()
    stock_repo = AsyncMock()

    transaction_repo.get_by_id.return_value = tx
    operation_repo.get_by_id_for_update.return_value = operation
    transaction_repo.check_all_transactions_completed.return_value = all_completed
    operation_repo.get_detailed.return_value = _make_detailed(
        op_id=operation.id,
        op_type=operation.operation_type,
        status=(
            OperationStatus.COMPLETED
            if all_completed
            else OperationStatus.IN_TRANSIT
            if operation.operation_type == OperationType.TRANSFER
            else operation.status
        ),
    )
    if out_transactions is not None:
        transaction_repo.get_transactions_by_type.return_value = out_transactions

    svc = _make_service(
        mock_conn,
        operation_repo=operation_repo,
        transaction_repo=transaction_repo,
        stock_repo=stock_repo,
    )
    return svc, operation_repo, transaction_repo, stock_repo


@pytest.mark.asyncio
async def test_complete_transaction_in_success(mock_conn, admin_user):
    """
    complete_transaction for a PENDING IN transaction with a matching
    received_quantity:
    - increments stock by the planned quantity
    - marks the transaction COMPLETED
    - detects all done → marks operation COMPLETED
    - returns OperationResponse
    """
    tx = _make_tx(tx_type=TransactionType.IN, status=TransactionStatus.PENDING, qty=10)
    op = _make_operation(status=OperationStatus.PENDING)

    svc, operation_repo, transaction_repo, stock_repo = _setup_complete_transaction(
        mock_conn, tx, op, all_completed=True
    )

    result = await svc.complete_transaction(
        operation_id=1,
        transaction_id=1,
        current_user=admin_user,
        received_quantity=10,
    )

    assert result.status == OperationStatus.COMPLETED
    stock_repo.increment.assert_awaited_once_with(
        product_id=1,
        warehouse_id=1,
        qty=10,
        tenant_id=admin_user.tenant_id,
        conn=mock_conn,
    )
    transaction_repo.update_transaction_status.assert_awaited_once_with(
        transaction_id=1,
        tenant_id=admin_user.tenant_id,
        movement_status=TransactionStatus.COMPLETED,
        conn=mock_conn,
    )


@pytest.mark.asyncio
async def test_complete_transaction_out_success(mock_conn, admin_user):
    """
    complete_transaction for a PENDING OUT transaction:
    - decrements stock
    - marks the transaction COMPLETED
    - marks the operation COMPLETED when all transactions are done
    """
    tx = _make_tx(tx_type=TransactionType.OUT, status=TransactionStatus.PENDING, qty=5)
    op = _make_operation(status=OperationStatus.PENDING)

    svc, _, transaction_repo, stock_repo = _setup_complete_transaction(
        mock_conn, tx, op, all_completed=True
    )

    result = await svc.complete_transaction(
        operation_id=1,
        transaction_id=1,
        current_user=admin_user,
        received_quantity=None,
    )

    assert result.status == OperationStatus.COMPLETED
    stock_repo.decrement.assert_awaited_once_with(
        product_id=1,
        warehouse_id=1,
        qty=5,
        tenant_id=admin_user.tenant_id,
        conn=mock_conn,
    )


@pytest.mark.asyncio
async def test_complete_transaction_not_found_raises_404(mock_conn, admin_user):
    """
    complete_transaction raises HTTP 404 when the transaction does not exist
    in the caller's tenant.
    """
    transaction_repo = AsyncMock()
    transaction_repo.get_by_id.return_value = None

    svc = _make_service(mock_conn, transaction_repo=transaction_repo)

    with pytest.raises(HTTPException) as exc:
        await svc.complete_transaction(
            operation_id=1,
            transaction_id=999,
            current_user=admin_user,
        )

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_complete_transaction_wrong_operation_raises_400(mock_conn, admin_user):
    """
    complete_transaction raises HTTP 400 when the transaction exists but belongs
    to a different operation than the one specified in the URL.
    """
    tx = _make_tx(tx_id=1, op_id=99)  # belongs to op 99, not op 1
    transaction_repo = AsyncMock()
    transaction_repo.get_by_id.return_value = tx

    svc = _make_service(mock_conn, transaction_repo=transaction_repo)

    with pytest.raises(HTTPException) as exc:
        await svc.complete_transaction(
            operation_id=1,  # different from tx.operation_id
            transaction_id=1,
            current_user=admin_user,
        )

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_complete_transaction_already_completed_raises_409(mock_conn, admin_user):
    """
    complete_transaction raises HTTP 409 when the transaction is already in
    COMPLETED state.  Re-applying stock mutations would corrupt inventory.
    """
    tx = _make_tx(status=TransactionStatus.COMPLETED)
    transaction_repo = AsyncMock()
    transaction_repo.get_by_id.return_value = tx

    svc = _make_service(mock_conn, transaction_repo=transaction_repo)

    with pytest.raises(HTTPException) as exc:
        await svc.complete_transaction(
            operation_id=1, transaction_id=1, current_user=admin_user
        )

    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_complete_transaction_already_failed_raises_409(mock_conn, admin_user):
    """
    complete_transaction raises HTTP 409 when the transaction is already FAILED.
    FAILED is a terminal state; completion would silently ignore the prior error.
    """
    tx = _make_tx(status=TransactionStatus.FAILED)
    transaction_repo = AsyncMock()
    transaction_repo.get_by_id.return_value = tx

    svc = _make_service(mock_conn, transaction_repo=transaction_repo)

    with pytest.raises(HTTPException) as exc:
        await svc.complete_transaction(
            operation_id=1, transaction_id=1, current_user=admin_user
        )

    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_complete_transaction_operation_completed_raises_409(
    mock_conn, admin_user
):
    """
    complete_transaction raises HTTP 409 when the parent operation is already
    COMPLETED.  No transaction line should be modifiable in a closed operation.
    """
    tx = _make_tx(status=TransactionStatus.PENDING)
    op = _make_operation(status=OperationStatus.COMPLETED)

    transaction_repo = AsyncMock()
    transaction_repo.get_by_id.return_value = tx
    operation_repo = AsyncMock()
    operation_repo.get_by_id_for_update.return_value = op

    svc = _make_service(
        mock_conn, operation_repo=operation_repo, transaction_repo=transaction_repo
    )

    with pytest.raises(HTTPException) as exc:
        await svc.complete_transaction(
            operation_id=1, transaction_id=1, current_user=admin_user,
            received_quantity=10,
        )

    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_complete_transaction_operation_cancelled_raises_409(
    mock_conn, admin_user
):
    """
    complete_transaction raises HTTP 409 when the parent operation is CANCELLED.
    Transactions within a cancelled operation must not be individually completed.
    """
    tx = _make_tx(status=TransactionStatus.PENDING)
    op = _make_operation(status=OperationStatus.CANCELLED)

    transaction_repo = AsyncMock()
    transaction_repo.get_by_id.return_value = tx
    operation_repo = AsyncMock()
    operation_repo.get_by_id_for_update.return_value = op

    svc = _make_service(
        mock_conn, operation_repo=operation_repo, transaction_repo=transaction_repo
    )

    with pytest.raises(HTTPException) as exc:
        await svc.complete_transaction(
            operation_id=1, transaction_id=1, current_user=admin_user
        )

    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_complete_transaction_in_without_received_qty_raises_400(
    mock_conn, admin_user
):
    """
    complete_transaction raises HTTP 400 (via ValueError→HTTPException cascade)
    when completing an IN transaction without providing received_quantity.
    IN transactions require a received_quantity to confirm physical receipt.
    """
    tx = _make_tx(tx_type=TransactionType.IN, status=TransactionStatus.PENDING)
    op = _make_operation(status=OperationStatus.PENDING)

    transaction_repo = AsyncMock()
    transaction_repo.get_by_id.return_value = tx
    operation_repo = AsyncMock()
    operation_repo.get_by_id_for_update.return_value = op
    transaction_repo.list_inventory_by_operation.return_value = [tx]

    svc = _make_service(
        mock_conn, operation_repo=operation_repo, transaction_repo=transaction_repo
    )

    with pytest.raises(HTTPException) as exc:
        await svc.complete_transaction(
            operation_id=1,
            transaction_id=1,
            current_user=admin_user,
            received_quantity=None,  # missing
        )

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_complete_transaction_received_qty_exceeds_planned_raises_400(
    mock_conn, admin_user
):
    """
    complete_transaction raises HTTP 400 when received_quantity exceeds the
    planned quantity on the transaction.  You cannot receive more than was
    ordered.
    """
    tx = _make_tx(tx_type=TransactionType.IN, status=TransactionStatus.PENDING, qty=10)
    op = _make_operation(status=OperationStatus.PENDING)

    transaction_repo = AsyncMock()
    transaction_repo.get_by_id.return_value = tx
    operation_repo = AsyncMock()
    operation_repo.get_by_id_for_update.return_value = op
    transaction_repo.list_inventory_by_operation.return_value = [tx]

    svc = _make_service(
        mock_conn, operation_repo=operation_repo, transaction_repo=transaction_repo
    )

    with pytest.raises(HTTPException) as exc:
        await svc.complete_transaction(
            operation_id=1,
            transaction_id=1,
            current_user=admin_user,
            received_quantity=999,  # exceeds planned qty=10
        )

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_complete_transaction_partial_receipt_updates_quantity(
    mock_conn, admin_user
):
    """
    When received_quantity < planned quantity, complete_transaction records a
    partial receipt:
    - calls update_transaction_quantity_and_note with the received amount
    - increments stock by the received (not planned) quantity
    """
    tx = _make_tx(tx_type=TransactionType.IN, status=TransactionStatus.PENDING, qty=10)
    op = _make_operation(status=OperationStatus.PENDING)

    updated_tx = _make_tx(
        tx_type=TransactionType.IN, status=TransactionStatus.PENDING, qty=6
    )

    transaction_repo = AsyncMock()
    transaction_repo.get_by_id.return_value = tx
    transaction_repo.update_transaction_quantity_and_note.return_value = updated_tx
    transaction_repo.check_all_transactions_completed.return_value = True

    operation_repo = AsyncMock()
    operation_repo.get_by_id_for_update.return_value = op
    operation_repo.get_detailed.return_value = _make_detailed(
        status=OperationStatus.COMPLETED
    )

    stock_repo = AsyncMock()

    svc = _make_service(
        mock_conn,
        operation_repo=operation_repo,
        transaction_repo=transaction_repo,
        stock_repo=stock_repo,
    )

    await svc.complete_transaction(
        operation_id=1,
        transaction_id=1,
        current_user=admin_user,
        received_quantity=6,  # partial receipt
    )

    transaction_repo.update_transaction_quantity_and_note.assert_awaited_once()
    # Stock incremented by 6 (the received qty, taken from updated_tx.quantity)
    stock_repo.increment.assert_awaited_once_with(
        product_id=1,
        warehouse_id=1,
        qty=6,
        tenant_id=admin_user.tenant_id,
        conn=mock_conn,
    )


@pytest.mark.asyncio
async def test_complete_transaction_stock_error_fails_tx_and_operation(
    mock_conn, admin_user
):
    """
    When the stock repository raises an exception during complete_transaction:
    - the transaction is marked FAILED
    - the operation is cascaded to CANCELLED
    - the endpoint raises HTTP 400
    """
    tx = _make_tx(tx_type=TransactionType.OUT, status=TransactionStatus.PENDING)
    op = _make_operation(status=OperationStatus.PENDING)

    transaction_repo = AsyncMock()
    transaction_repo.get_by_id.return_value = tx
    transaction_repo.list_inventory_by_operation.return_value = [tx]

    operation_repo = AsyncMock()
    operation_repo.get_by_id_for_update.return_value = op

    stock_repo = AsyncMock()
    stock_repo.decrement.side_effect = ValueError("Insufficient stock")

    svc = _make_service(
        mock_conn,
        operation_repo=operation_repo,
        transaction_repo=transaction_repo,
        stock_repo=stock_repo,
    )

    with pytest.raises(HTTPException) as exc:
        await svc.complete_transaction(
            operation_id=1, transaction_id=1, current_user=admin_user
        )

    assert exc.value.status_code == 400
    # Transaction must be marked FAILED
    transaction_repo.update_transaction_status.assert_any_await(
        transaction_id=1,
        tenant_id=admin_user.tenant_id,
        movement_status=TransactionStatus.FAILED,
        conn=mock_conn,
    )
    # Operation must be cancelled
    operation_repo.update_status.assert_awaited_with(
        operation_id=1,
        tenant_id=admin_user.tenant_id,
        status=OperationStatus.CANCELLED,
        conn=mock_conn,
    )


@pytest.mark.asyncio
async def test_complete_transaction_transfer_in_blocked_before_out_resolved(
    mock_conn, admin_user
):
    """
    For TRANSFER operations, completing the IN transaction is blocked until
    all OUT transactions are completed.  If any OUT is still PENDING,
    complete_transaction raises HTTP 409.
    """
    in_tx = _make_tx(tx_id=2, tx_type=TransactionType.IN, status=TransactionStatus.PENDING)
    pending_out_tx = _make_tx(tx_id=1, tx_type=TransactionType.OUT, status=TransactionStatus.PENDING)
    op = _make_operation(op_type=OperationType.TRANSFER, status=OperationStatus.PENDING)

    transaction_repo = AsyncMock()
    transaction_repo.get_by_id.return_value = in_tx
    transaction_repo.list_inventory_by_operation.return_value = [
        pending_out_tx,
        in_tx,
    ]  # OUT still PENDING

    operation_repo = AsyncMock()
    operation_repo.get_by_id_for_update.return_value = op

    svc = _make_service(
        mock_conn, operation_repo=operation_repo, transaction_repo=transaction_repo
    )

    with pytest.raises(HTTPException) as exc:
        await svc.complete_transaction(
            operation_id=1,
            transaction_id=2,
            current_user=admin_user,
            received_quantity=10,
        )

    assert exc.value.status_code == 409
    assert "OUT" in exc.value.detail


@pytest.mark.asyncio
async def test_complete_transaction_transfer_out_sets_in_transit(
    mock_conn, admin_user
):
    """
    For TRANSFER operations, completing the OUT transaction and detecting that
    all OUT lines are done (but IN is still pending) must transition the
    operation to IN_TRANSIT.
    """
    out_tx = _make_tx(tx_id=1, tx_type=TransactionType.OUT, status=TransactionStatus.PENDING)
    completed_out = _make_tx(tx_id=1, tx_type=TransactionType.OUT, status=TransactionStatus.COMPLETED)
    op = _make_operation(
        op_type=OperationType.TRANSFER,
        status=OperationStatus.PENDING,
        source_id=1,
        dest_id=2,
    )

    transaction_repo = AsyncMock()
    transaction_repo.get_by_id.return_value = out_tx
    transaction_repo.check_all_transactions_completed.return_value = False  # IN still pending
    transaction_repo.get_transactions_by_type.return_value = [completed_out]

    operation_repo = AsyncMock()
    operation_repo.get_by_id_for_update.return_value = op
    operation_repo.get_detailed.return_value = _make_detailed(
        op_type=OperationType.TRANSFER, status=OperationStatus.IN_TRANSIT
    )

    svc = _make_service(
        mock_conn,
        operation_repo=operation_repo,
        transaction_repo=transaction_repo,
        stock_repo=AsyncMock(),
    )

    result = await svc.complete_transaction(
        operation_id=1, transaction_id=1, current_user=admin_user
    )

    assert result.status == OperationStatus.IN_TRANSIT
    operation_repo.update_status.assert_awaited_once_with(
        operation_id=1,
        tenant_id=admin_user.tenant_id,
        status=OperationStatus.IN_TRANSIT,
        conn=mock_conn,
    )


@pytest.mark.asyncio
async def test_complete_transaction_all_done_marks_operation_completed(
    mock_conn, admin_user
):
    """
    When check_all_transactions_completed returns True after completing a
    transaction, update_status is called with COMPLETED on the operation.
    """
    tx = _make_tx(tx_type=TransactionType.OUT, status=TransactionStatus.PENDING)
    op = _make_operation(status=OperationStatus.PENDING)

    transaction_repo = AsyncMock()
    transaction_repo.get_by_id.return_value = tx
    transaction_repo.check_all_transactions_completed.return_value = True

    operation_repo = AsyncMock()
    operation_repo.get_by_id_for_update.return_value = op
    operation_repo.get_detailed.return_value = _make_detailed(
        status=OperationStatus.COMPLETED
    )

    svc = _make_service(
        mock_conn,
        operation_repo=operation_repo,
        transaction_repo=transaction_repo,
        stock_repo=AsyncMock(),
    )

    await svc.complete_transaction(
        operation_id=1, transaction_id=1, current_user=admin_user
    )

    operation_repo.update_status.assert_awaited_once_with(
        operation_id=1,
        tenant_id=admin_user.tenant_id,
        status=OperationStatus.COMPLETED,
        conn=mock_conn,
    )


# ─── fail_transaction ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fail_transaction_success_cascades_to_operation(mock_conn, admin_user):
    """
    fail_transaction marks the target tx FAILED, cascades CANCELLED to the
    operation, and marks all remaining non-terminal sibling transactions FAILED.
    Returns the full OperationResponse.
    """
    pending_tx = _make_tx(tx_id=1, status=TransactionStatus.PENDING)
    sibling_tx = _make_tx(tx_id=2, status=TransactionStatus.PENDING)

    transaction_repo = AsyncMock()
    transaction_repo.get_by_id.return_value = pending_tx
    transaction_repo.list_inventory_by_operation.return_value = [
        pending_tx, sibling_tx
    ]

    operation_repo = AsyncMock()
    operation_repo.get_detailed.return_value = _make_detailed(
        status=OperationStatus.CANCELLED
    )

    svc = _make_service(
        mock_conn, operation_repo=operation_repo, transaction_repo=transaction_repo
    )
    result = await svc.fail_transaction(
        operation_id=1, transaction_id=1, current_user=admin_user
    )

    assert result.status == OperationStatus.CANCELLED
    # Target tx marked FAILED
    transaction_repo.update_transaction_status.assert_any_await(
        transaction_id=1,
        tenant_id=admin_user.tenant_id,
        movement_status=TransactionStatus.FAILED,
        conn=mock_conn,
    )
    # Operation cancelled
    operation_repo.update_status.assert_awaited_once_with(
        operation_id=1,
        tenant_id=admin_user.tenant_id,
        status=OperationStatus.CANCELLED,
        conn=mock_conn,
    )


@pytest.mark.asyncio
async def test_fail_transaction_not_found_raises_404(mock_conn, admin_user):
    """
    fail_transaction raises HTTP 404 when the transaction does not exist in
    the caller's tenant.
    """
    transaction_repo = AsyncMock()
    transaction_repo.get_by_id.return_value = None

    svc = _make_service(mock_conn, transaction_repo=transaction_repo)

    with pytest.raises(HTTPException) as exc:
        await svc.fail_transaction(
            operation_id=1, transaction_id=999, current_user=admin_user
        )

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_fail_transaction_wrong_operation_raises_400(mock_conn, admin_user):
    """
    fail_transaction raises HTTP 400 when the transaction does not belong to
    the specified operation.
    """
    tx = _make_tx(tx_id=1, op_id=99)  # belongs to op 99
    transaction_repo = AsyncMock()
    transaction_repo.get_by_id.return_value = tx

    svc = _make_service(mock_conn, transaction_repo=transaction_repo)

    with pytest.raises(HTTPException) as exc:
        await svc.fail_transaction(
            operation_id=1,  # different
            transaction_id=1,
            current_user=admin_user,
        )

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_fail_transaction_already_completed_raises_409(mock_conn, admin_user):
    """
    fail_transaction raises HTTP 409 when the transaction is already COMPLETED.
    Completed transactions are immutable; their stock effects cannot be undone.
    """
    tx = _make_tx(status=TransactionStatus.COMPLETED)
    transaction_repo = AsyncMock()
    transaction_repo.get_by_id.return_value = tx

    svc = _make_service(mock_conn, transaction_repo=transaction_repo)

    with pytest.raises(HTTPException) as exc:
        await svc.fail_transaction(
            operation_id=1, transaction_id=1, current_user=admin_user
        )

    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_fail_transaction_already_failed_raises_409(mock_conn, admin_user):
    """
    fail_transaction raises HTTP 409 when the transaction is already FAILED.
    Re-failing a failed transaction is a no-op that the service explicitly rejects.
    """
    tx = _make_tx(status=TransactionStatus.FAILED)
    transaction_repo = AsyncMock()
    transaction_repo.get_by_id.return_value = tx

    svc = _make_service(mock_conn, transaction_repo=transaction_repo)

    with pytest.raises(HTTPException) as exc:
        await svc.fail_transaction(
            operation_id=1, transaction_id=1, current_user=admin_user
        )

    assert exc.value.status_code == 409


# ─── _compose_transaction_note (sync unit tests) ─────────────────────────────


def test_compose_note_transfer_out():
    """
    TRANSFER + OUT produces a note describing a dispatch from source to
    destination warehouse.  Both warehouse names must appear in the note.
    """
    svc = OperationService.__new__(OperationService)
    note = svc._compose_transaction_note(
        operation_type=OperationType.TRANSFER,
        transaction_type=TransactionType.OUT,
        item_warehouse_name="WH-A",
        source_name="WH-A",
        destination_name="WH-B",
        user_note=None,
    )
    assert "dispatch" in note.lower() or "from" in note.lower()
    assert "WH-A" in note
    assert "WH-B" in note


def test_compose_note_transfer_in():
    """
    TRANSFER + IN produces a note describing a receipt at the destination
    warehouse.  Both warehouse names must appear in the note.
    """
    svc = OperationService.__new__(OperationService)
    note = svc._compose_transaction_note(
        operation_type=OperationType.TRANSFER,
        transaction_type=TransactionType.IN,
        item_warehouse_name="WH-B",
        source_name="WH-A",
        destination_name="WH-B",
        user_note=None,
    )
    assert "receive" in note.lower() or "at" in note.lower()
    assert "WH-A" in note
    assert "WH-B" in note


def test_compose_note_non_transfer_includes_warehouse():
    """
    Non-TRANSFER operations include the operation type, transaction type, and
    the item warehouse name in the generated note.
    """
    svc = OperationService.__new__(OperationService)
    note = svc._compose_transaction_note(
        operation_type=OperationType.PURCHASE,
        transaction_type=TransactionType.IN,
        item_warehouse_name="Main Warehouse",
        source_name=None,
        destination_name=None,
        user_note=None,
    )
    assert "Purchase" in note
    assert "Main Warehouse" in note


def test_compose_note_appends_user_note():
    """
    When a user_note is provided, it is appended to the auto-generated base
    note with a pipe separator.
    """
    svc = OperationService.__new__(OperationService)
    note = svc._compose_transaction_note(
        operation_type=OperationType.SALE,
        transaction_type=TransactionType.OUT,
        item_warehouse_name="WH-X",
        source_name=None,
        destination_name=None,
        user_note="Urgent order",
    )
    assert "Urgent order" in note
    assert "|" in note


def test_compose_note_no_warehouse_name():
    """
    When no item warehouse name is available, the note is still generated
    without raising — warehouse part is simply omitted.
    """
    svc = OperationService.__new__(OperationService)
    note = svc._compose_transaction_note(
        operation_type=OperationType.ADJUSTMENT,
        transaction_type=TransactionType.IN,
        item_warehouse_name=None,
        source_name=None,
        destination_name=None,
        user_note=None,
    )
    assert "Adjustment" in note
    assert note  # non-empty


# ─── _ensure_transfer_out_resolved_before_in (sync unit tests) ───────────────


def test_ensure_out_resolved_pending_raises_409():
    """
    _ensure_transfer_out_resolved_before_in raises HTTP 409 when any OUT
    transaction is still PENDING (not yet dispatched from source).
    """
    svc = OperationService.__new__(OperationService)
    items = [
        _make_tx(tx_id=1, tx_type=TransactionType.OUT, status=TransactionStatus.PENDING),
        _make_tx(tx_id=2, tx_type=TransactionType.IN, status=TransactionStatus.PENDING),
    ]
    with pytest.raises(HTTPException) as exc:
        svc._ensure_transfer_out_resolved_before_in(items)
    assert exc.value.status_code == 409


def test_ensure_out_resolved_draft_raises_409():
    """
    _ensure_transfer_out_resolved_before_in raises HTTP 409 when any OUT
    transaction is in DRAFT state (not yet committed for dispatch).
    """
    svc = OperationService.__new__(OperationService)
    items = [
        _make_tx(tx_id=1, tx_type=TransactionType.OUT, status=TransactionStatus.DRAFT),
        _make_tx(tx_id=2, tx_type=TransactionType.IN, status=TransactionStatus.PENDING),
    ]
    with pytest.raises(HTTPException) as exc:
        svc._ensure_transfer_out_resolved_before_in(items)
    assert exc.value.status_code == 409


def test_ensure_out_resolved_failed_out_raises_409():
    """
    _ensure_transfer_out_resolved_before_in raises HTTP 409 when any OUT
    transaction is FAILED.  A failed dispatch means the IN cannot be accepted.
    """
    svc = OperationService.__new__(OperationService)
    items = [
        _make_tx(tx_id=1, tx_type=TransactionType.OUT, status=TransactionStatus.FAILED),
        _make_tx(tx_id=2, tx_type=TransactionType.IN, status=TransactionStatus.PENDING),
    ]
    with pytest.raises(HTTPException) as exc:
        svc._ensure_transfer_out_resolved_before_in(items)
    assert exc.value.status_code == 409


def test_ensure_out_resolved_all_completed_passes():
    """
    _ensure_transfer_out_resolved_before_in does NOT raise when all OUT
    transactions are COMPLETED — the inbound leg is safe to process.
    """
    svc = OperationService.__new__(OperationService)
    items = [
        _make_tx(tx_id=1, tx_type=TransactionType.OUT, status=TransactionStatus.COMPLETED),
        _make_tx(tx_id=2, tx_type=TransactionType.IN, status=TransactionStatus.PENDING),
    ]
    # Must not raise
    svc._ensure_transfer_out_resolved_before_in(items)


# ─── _validate_transfer_in_quantity (sync unit tests) ────────────────────────


def test_validate_transfer_in_qty_exceeds_available_raises_400():
    """
    _validate_transfer_in_quantity raises HTTP 400 when the requested inbound
    quantity exceeds the completed-OUT quantity available to receive.
    """
    svc = OperationService.__new__(OperationService)
    in_tx = _make_tx(tx_id=2, tx_type=TransactionType.IN, status=TransactionStatus.PENDING, qty=10)
    out_tx = _make_tx(tx_id=1, tx_type=TransactionType.OUT, status=TransactionStatus.COMPLETED, qty=5)

    with pytest.raises(HTTPException) as exc:
        svc._validate_transfer_in_quantity(in_tx, [out_tx, in_tx], requested_in_quantity=10)

    assert exc.value.status_code == 400


def test_validate_transfer_in_qty_equals_available_passes():
    """
    _validate_transfer_in_quantity does NOT raise when requested_in_quantity
    equals the available completed-OUT quantity exactly.
    """
    svc = OperationService.__new__(OperationService)
    in_tx = _make_tx(tx_id=2, tx_type=TransactionType.IN, status=TransactionStatus.PENDING, qty=5)
    out_tx = _make_tx(tx_id=1, tx_type=TransactionType.OUT, status=TransactionStatus.COMPLETED, qty=5)

    # Must not raise
    svc._validate_transfer_in_quantity(in_tx, [out_tx, in_tx], requested_in_quantity=5)


def test_validate_transfer_in_qty_within_available_passes():
    """
    _validate_transfer_in_quantity does NOT raise when requested_in_quantity
    is less than the available completed-OUT quantity (partial receipt).
    """
    svc = OperationService.__new__(OperationService)
    in_tx = _make_tx(tx_id=2, tx_type=TransactionType.IN, status=TransactionStatus.PENDING, qty=10)
    out_tx = _make_tx(tx_id=1, tx_type=TransactionType.OUT, status=TransactionStatus.COMPLETED, qty=15)

    # Must not raise
    svc._validate_transfer_in_quantity(in_tx, [out_tx, in_tx], requested_in_quantity=10)
