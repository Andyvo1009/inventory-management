"""
Unit tests for TransactionService.

TransactionService is a thin read-only façade over TransactionRepository.
Direct transaction creation via this service was deprecated in favour of the
operation-first workflow; `create_transaction` now unconditionally raises
HTTP 410 Gone.

Coverage map
─────────────────────────────────────────────────────────────────────────────
create_transaction
  • Always raises HTTP 410 Gone regardless of payload              (1 test)
  • No repository or stock side-effects are triggered             (1 test)

get_transaction_by_id
  • Returns TransactionResponse when the transaction exists        (1 test)
  • Raises HTTP 404 when the transaction does not exist           (1 test)

list_transactions
  • Returns a populated TransactionListResponse                   (1 test)
  • Forwards all filter parameters verbatim to the repository     (1 test)
  • Returns total=0 and empty list when no rows match             (1 test)
  • Warehouse filter is forwarded correctly                       (1 test)

list_transactions_by_operation
  • Returns all transactions for the given operation              (1 test)
  • Returns total=0 when the operation has no transactions        (1 test)
  • limit equals len(transactions), offset is always 0           (1 test)
─────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from models.models import TransactionType
from schemas.transaction_schema import (
    TransactionCreateRequest,
    TransactionListRequest,
    TransactionResponse,
)
from services.transaction_service import TransactionService


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _make_service(
    mock_conn,
    transaction_repo=None,
    product_repo=None,
    warehouse_repo=None,
    stock_repo=None,
) -> TransactionService:
    """Construct a TransactionService with every dependency replaced by mocks."""
    return TransactionService(
        mock_conn,
        transaction_repo=transaction_repo or AsyncMock(),
        product_repo=product_repo or AsyncMock(),
        warehouse_repo=warehouse_repo or AsyncMock(),
        stock_repo=stock_repo or AsyncMock(),
    )


def _transaction_row(
    tx_type: TransactionType = TransactionType.IN,
    origin_id: int | None = None,
    origin_name: str | None = None,
    dest_id: int | None = 1,
    dest_name: str | None = "Main Warehouse",
    operation_id: int = 1,
    movement_status: str = "Completed",
) -> dict:
    """
    Build a dict that satisfies TransactionResponse validation.

    All fields required by TransactionResponse are present, including
    `operation_id` and `movement_status` which were added to the schema
    after the operation-first workflow was introduced.
    """
    return {
        "id": 1,
        "tenant_id": 1,
        "type": tx_type,
        "product_id": 1,
        "product_name": "Test Product",
        "product_sku": "SKU-001",
        "operation_id": operation_id,
        "quantity": 10,
        "origin_warehouse_id": origin_id,
        "origin_warehouse_name": origin_name,
        "des_warehouse_id": dest_id,
        "des_warehouse_name": dest_name,
        "user_id": 1,
        "user_name": "Admin User",
        "note": None,
        "timestamp": datetime(2024, 6, 1, 12, 0, 0),
        "movement_status": movement_status,
    }


def _make_tx_response(**kwargs) -> TransactionResponse:
    """Return a TransactionResponse built from _transaction_row defaults, with overrides."""
    return TransactionResponse(**{**_transaction_row(), **kwargs})


# ─── create_transaction (deprecated — always HTTP 410) ───────────────────────


@pytest.mark.asyncio
async def test_create_transaction_raises_410(mock_conn, admin_user):
    """
    create_transaction must raise HTTP 410 Gone.

    Direct transaction creation was removed in favour of the operation-first
    workflow (/api/operations).  Any call — regardless of the payload — must
    immediately raise HTTP 410 and never reach the repository layer.
    """
    service = _make_service(mock_conn)
    data = TransactionCreateRequest(
        product_id=1,
        type=TransactionType.IN,
        quantity=10,
        des_warehouse_id=1,
    )

    with pytest.raises(HTTPException) as exc:
        await service.create_transaction(data, admin_user)

    assert exc.value.status_code == 410
    assert "deprecated" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_create_transaction_has_no_side_effects(mock_conn, admin_user):
    """
    create_transaction must not call any repository or stock-mutation method.

    Because the endpoint raises 410 before any business logic runs, all
    injected mocks must remain uncalled.
    """
    transaction_repo = AsyncMock()
    stock_repo = AsyncMock()
    product_repo = AsyncMock()
    warehouse_repo = AsyncMock()

    service = _make_service(
        mock_conn,
        transaction_repo=transaction_repo,
        stock_repo=stock_repo,
        product_repo=product_repo,
        warehouse_repo=warehouse_repo,
    )
    data = TransactionCreateRequest(
        product_id=1,
        type=TransactionType.OUT,
        quantity=5,
        origin_warehouse_id=1,
    )

    with pytest.raises(HTTPException):
        await service.create_transaction(data, admin_user)

    transaction_repo.record.assert_not_called()
    stock_repo.decrement.assert_not_called()
    stock_repo.increment.assert_not_called()
    product_repo.get_by_id.assert_not_called()
    warehouse_repo.get_by_id.assert_not_called()


# ─── get_transaction_by_id ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_transaction_by_id_success(
    mock_conn, admin_user, sample_transaction_row
):
    """
    get_transaction_by_id returns the TransactionResponse from the repository
    when the requested transaction exists for the caller's tenant.
    """
    expected = TransactionResponse(**sample_transaction_row)
    transaction_repo = AsyncMock()
    transaction_repo.get_by_id_detailed.return_value = expected

    service = _make_service(mock_conn, transaction_repo=transaction_repo)
    result = await service.get_transaction_by_id(1, admin_user)

    assert result.id == 1
    assert result.product_sku == "SKU-001"
    assert result.type == TransactionType.IN
    transaction_repo.get_by_id_detailed.assert_awaited_once_with(
        tx_id=1, tenant_id=admin_user.tenant_id
    )


@pytest.mark.asyncio
async def test_get_transaction_by_id_not_found_raises_404(mock_conn, admin_user):
    """
    get_transaction_by_id raises HTTP 404 when the repository returns None,
    meaning no transaction with that ID exists in the caller's tenant.
    """
    transaction_repo = AsyncMock()
    transaction_repo.get_by_id_detailed.return_value = None

    service = _make_service(mock_conn, transaction_repo=transaction_repo)

    with pytest.raises(HTTPException) as exc:
        await service.get_transaction_by_id(999, admin_user)

    assert exc.value.status_code == 404


# ─── list_transactions ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_transactions_success(mock_conn, admin_user, sample_transaction_row):
    """
    list_transactions wraps the repository result in a TransactionListResponse
    with total equal to the number of returned rows.
    """
    tx = TransactionResponse(**sample_transaction_row)
    transaction_repo = AsyncMock()
    transaction_repo.list_by_tenant.return_value = [tx]

    service = _make_service(mock_conn, transaction_repo=transaction_repo)
    result = await service.list_transactions(TransactionListRequest(), admin_user)

    assert result.total == 1
    assert result.transactions[0].product_sku == "SKU-001"


@pytest.mark.asyncio
async def test_list_transactions_with_filters(mock_conn, admin_user):
    """
    list_transactions forwards all filter fields — type, warehouse_id, product_id,
    limit, offset — verbatim to the repository without any transformation.
    """
    transaction_repo = AsyncMock()
    transaction_repo.list_by_tenant.return_value = []

    service = _make_service(mock_conn, transaction_repo=transaction_repo)
    filters = TransactionListRequest(
        type=TransactionType.IN,
        product_id=1,
        limit=10,
        offset=5,
    )

    result = await service.list_transactions(filters, admin_user)

    transaction_repo.list_by_tenant.assert_awaited_once_with(
        tenant_id=admin_user.tenant_id,
        type=TransactionType.IN,
        warehouse_id=None,
        product_id=1,
        limit=10,
        offset=5,
    )
    assert result.total == 0
    assert result.limit == 10
    assert result.offset == 5


@pytest.mark.asyncio
async def test_list_transactions_empty_results(mock_conn, admin_user):
    """
    list_transactions with no matching rows returns total=0 and an empty list.
    This verifies the service handles the empty-set case without raising.
    """
    transaction_repo = AsyncMock()
    transaction_repo.list_by_tenant.return_value = []

    service = _make_service(mock_conn, transaction_repo=transaction_repo)
    result = await service.list_transactions(TransactionListRequest(), admin_user)

    assert result.total == 0
    assert result.transactions == []


@pytest.mark.asyncio
async def test_list_transactions_warehouse_filter_forwarded(mock_conn, admin_user):
    """
    When a warehouse_id filter is provided, it is forwarded to list_by_tenant
    without modification so the repository can apply the correct WHERE clause.
    """
    transaction_repo = AsyncMock()
    transaction_repo.list_by_tenant.return_value = []

    service = _make_service(mock_conn, transaction_repo=transaction_repo)
    filters = TransactionListRequest(warehouse_id=7)

    await service.list_transactions(filters, admin_user)

    _, kwargs = transaction_repo.list_by_tenant.call_args
    assert kwargs["warehouse_id"] == 7


# ─── list_transactions_by_operation ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_transactions_by_operation_success(
    mock_conn, admin_user, sample_transaction_row
):
    """
    list_transactions_by_operation returns all transaction rows that belong
    to the given operation_id, wrapped in a TransactionListResponse.
    total equals the length of the returned list.
    """
    tx = TransactionResponse(**sample_transaction_row)
    transaction_repo = AsyncMock()
    transaction_repo.list_by_operation.return_value = [tx]

    service = _make_service(mock_conn, transaction_repo=transaction_repo)
    result = await service.list_transactions_by_operation(
        operation_id=1, current_user=admin_user
    )

    assert result.total == 1
    assert result.transactions[0].id == 1
    transaction_repo.list_by_operation.assert_awaited_once_with(
        operation_id=1, tenant_id=admin_user.tenant_id
    )


@pytest.mark.asyncio
async def test_list_transactions_by_operation_empty(mock_conn, admin_user):
    """
    list_transactions_by_operation returns total=0 and an empty list when
    the operation has no associated transactions.
    """
    transaction_repo = AsyncMock()
    transaction_repo.list_by_operation.return_value = []

    service = _make_service(mock_conn, transaction_repo=transaction_repo)
    result = await service.list_transactions_by_operation(
        operation_id=42, current_user=admin_user
    )

    assert result.total == 0
    assert result.transactions == []


@pytest.mark.asyncio
async def test_list_transactions_by_operation_limit_equals_count(
    mock_conn, admin_user, sample_transaction_row
):
    """
    list_transactions_by_operation sets limit to len(transactions) and
    offset to 0, because this endpoint always returns all rows for the
    operation without pagination.
    """
    txs = [
        TransactionResponse(**{**sample_transaction_row, "id": i})
        for i in range(1, 4)
    ]
    transaction_repo = AsyncMock()
    transaction_repo.list_by_operation.return_value = txs

    service = _make_service(mock_conn, transaction_repo=transaction_repo)
    result = await service.list_transactions_by_operation(
        operation_id=1, current_user=admin_user
    )

    assert result.total == 3
    assert result.limit == 3
    assert result.offset == 0
