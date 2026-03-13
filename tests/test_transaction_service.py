"""
Unit tests for TransactionService.

Covers: create transaction (IN / OUT / TRANSFER), warehouse/product validation,
stock mutations, insufficient-stock guard, list, and get by ID.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from models.models import TransactionType
from schemas.transaction_schema import TransactionCreateRequest, TransactionListRequest
from services.transaction_service import TransactionService


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _make_service(
    mock_conn,
    transaction_repo=None,
    product_repo=None,
    warehouse_repo=None,
    stock_repo=None,
) -> TransactionService:
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
) -> dict:
    return {
        "id": 1,
        "tenant_id": 1,
        "type": tx_type,
        "product_id": 1,
        "product_name": "Test Product",
        "product_sku": "SKU-001",
        "quantity": 10,
        "origin_warehouse_id": origin_id,
        "origin_warehouse_name": origin_name,
        "des_warehouse_id": dest_id,
        "des_warehouse_name": dest_name,
        "user_id": 1,
        "user_name": "Admin User",
        "notes": None,
        "timestamp": datetime(2024, 6, 1, 12, 0, 0),
    }


# ─── create_transaction: IN ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_in_transaction_success(
    mock_conn, admin_user, sample_warehouse, sample_transaction_row
):
    # Product exists
    mock_conn.fetchrow.side_effect = [
        {"id": 1},             # product check
        sample_transaction_row,  # final SELECT
    ]

    warehouse_repo = AsyncMock()
    warehouse_repo.get_by_id.return_value = sample_warehouse

    stock_repo = AsyncMock()
    transaction_repo = AsyncMock()

    service = _make_service(
        mock_conn,
        transaction_repo=transaction_repo,
        warehouse_repo=warehouse_repo,
        stock_repo=stock_repo,
    )
    data = TransactionCreateRequest(
        product_id=1,
        type=TransactionType.IN,
        quantity=10,
        des_warehouse_id=1,
    )

    result = await service.create_transaction(data, admin_user)

    assert result.type == TransactionType.IN
    assert result.quantity == 10
    stock_repo.increment.assert_called_once_with(
        product_id=1, warehouse_id=1, qty=10, conn=mock_conn
    )
    transaction_repo.record.assert_called_once()


@pytest.mark.asyncio
async def test_create_in_transaction_missing_dest_raises_400(
    mock_conn, admin_user
):
    mock_conn.fetchrow.return_value = {"id": 1}  # product exists

    service = _make_service(mock_conn)
    data = TransactionCreateRequest(
        product_id=1,
        type=TransactionType.IN,
        quantity=5,
        des_warehouse_id=None,  # missing
    )

    with pytest.raises(HTTPException) as exc:
        await service.create_transaction(data, admin_user)

    assert exc.value.status_code == 400
    assert "des_warehouse_id" in exc.value.detail


# ─── create_transaction: OUT ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_out_transaction_success(
    mock_conn, admin_user, sample_warehouse
):
    out_row = _transaction_row(
        tx_type=TransactionType.OUT,
        origin_id=1,
        origin_name="Main Warehouse",
        dest_id=None,
        dest_name=None,
    )
    mock_conn.fetchrow.side_effect = [{"id": 1}, out_row]

    warehouse_repo = AsyncMock()
    warehouse_repo.get_by_id.return_value = sample_warehouse

    stock_repo = AsyncMock()
    transaction_repo = AsyncMock()

    service = _make_service(
        mock_conn,
        transaction_repo=transaction_repo,
        warehouse_repo=warehouse_repo,
        stock_repo=stock_repo,
    )
    data = TransactionCreateRequest(
        product_id=1,
        type=TransactionType.OUT,
        quantity=5,
        origin_warehouse_id=1,
    )

    result = await service.create_transaction(data, admin_user)

    assert result.type == TransactionType.OUT
    stock_repo.decrement.assert_called_once_with(
        product_id=1, warehouse_id=1, qty=5, conn=mock_conn
    )


@pytest.mark.asyncio
async def test_create_out_transaction_missing_origin_raises_400(
    mock_conn, admin_user
):
    mock_conn.fetchrow.return_value = {"id": 1}

    service = _make_service(mock_conn)
    data = TransactionCreateRequest(
        product_id=1,
        type=TransactionType.OUT,
        quantity=5,
        origin_warehouse_id=None,  # missing
    )

    with pytest.raises(HTTPException) as exc:
        await service.create_transaction(data, admin_user)

    assert exc.value.status_code == 400
    assert "origin_warehouse_id" in exc.value.detail


@pytest.mark.asyncio
async def test_create_out_transaction_insufficient_stock_raises_400(
    mock_conn, admin_user, sample_warehouse
):
    mock_conn.fetchrow.return_value = {"id": 1}

    warehouse_repo = AsyncMock()
    warehouse_repo.get_by_id.return_value = sample_warehouse

    stock_repo = AsyncMock()
    stock_repo.decrement.side_effect = ValueError("Insufficient stock")

    service = _make_service(
        mock_conn,
        warehouse_repo=warehouse_repo,
        stock_repo=stock_repo,
    )
    data = TransactionCreateRequest(
        product_id=1,
        type=TransactionType.OUT,
        quantity=9999,
        origin_warehouse_id=1,
    )

    with pytest.raises(HTTPException) as exc:
        await service.create_transaction(data, admin_user)

    assert exc.value.status_code == 400
    assert "Insufficient" in exc.value.detail


# ─── create_transaction: TRANSFER ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_transfer_transaction_success(
    mock_conn, admin_user, sample_warehouse, sample_warehouse_b
):
    transfer_row = _transaction_row(
        tx_type=TransactionType.TRANSFER,
        origin_id=1,
        origin_name="Main Warehouse",
        dest_id=2,
        dest_name="Secondary Warehouse",
    )
    mock_conn.fetchrow.side_effect = [{"id": 1}, transfer_row]

    warehouse_repo = AsyncMock()
    warehouse_repo.get_by_id.side_effect = [sample_warehouse, sample_warehouse_b]

    stock_repo = AsyncMock()
    transaction_repo = AsyncMock()

    service = _make_service(
        mock_conn,
        transaction_repo=transaction_repo,
        warehouse_repo=warehouse_repo,
        stock_repo=stock_repo,
    )
    data = TransactionCreateRequest(
        product_id=1,
        type=TransactionType.TRANSFER,
        quantity=10,
        origin_warehouse_id=1,
        des_warehouse_id=2,
    )

    result = await service.create_transaction(data, admin_user)

    assert result.type == TransactionType.TRANSFER
    stock_repo.decrement.assert_called_once_with(
        product_id=1, warehouse_id=1, qty=10, conn=mock_conn
    )
    stock_repo.increment.assert_called_once_with(
        product_id=1, warehouse_id=2, qty=10, conn=mock_conn
    )


@pytest.mark.asyncio
async def test_create_transfer_missing_warehouses_raises_400(mock_conn, admin_user):
    mock_conn.fetchrow.return_value = {"id": 1}

    service = _make_service(mock_conn)
    data = TransactionCreateRequest(
        product_id=1,
        type=TransactionType.TRANSFER,
        quantity=5,
        origin_warehouse_id=None,  # missing both
        des_warehouse_id=None,
    )

    with pytest.raises(HTTPException) as exc:
        await service.create_transaction(data, admin_user)

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_create_transfer_same_warehouse_raises_400(
    mock_conn, admin_user
):
    mock_conn.fetchrow.return_value = {"id": 1}

    service = _make_service(mock_conn)
    data = TransactionCreateRequest(
        product_id=1,
        type=TransactionType.TRANSFER,
        quantity=5,
        origin_warehouse_id=1,
        des_warehouse_id=1,  # same as origin
    )

    with pytest.raises(HTTPException) as exc:
        await service.create_transaction(data, admin_user)

    assert exc.value.status_code == 400
    assert "different" in exc.value.detail


# ─── create_transaction: product / warehouse not found ───────────────────────


@pytest.mark.asyncio
async def test_create_transaction_product_not_found_raises_404(
    mock_conn, admin_user
):
    mock_conn.fetchrow.return_value = None  # product not found

    service = _make_service(mock_conn)
    data = TransactionCreateRequest(
        product_id=999,
        type=TransactionType.IN,
        quantity=5,
        des_warehouse_id=1,
    )

    with pytest.raises(HTTPException) as exc:
        await service.create_transaction(data, admin_user)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_create_in_transaction_dest_warehouse_not_found_raises_404(
    mock_conn, admin_user
):
    mock_conn.fetchrow.return_value = {"id": 1}  # product exists

    warehouse_repo = AsyncMock()
    warehouse_repo.get_by_id.return_value = None  # warehouse missing

    service = _make_service(mock_conn, warehouse_repo=warehouse_repo)
    data = TransactionCreateRequest(
        product_id=1,
        type=TransactionType.IN,
        quantity=5,
        des_warehouse_id=99,
    )

    with pytest.raises(HTTPException) as exc:
        await service.create_transaction(data, admin_user)

    assert exc.value.status_code == 404


# ─── get_transaction_by_id ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_transaction_by_id_success(
    mock_conn, admin_user, sample_transaction_row
):
    from schemas.transaction_schema import TransactionResponse

    transaction_repo = AsyncMock()
    transaction_repo.get_by_id_detailed.return_value = TransactionResponse(
        **sample_transaction_row
    )

    service = _make_service(mock_conn, transaction_repo=transaction_repo)
    result = await service.get_transaction_by_id(1, admin_user)

    assert result.id == 1
    assert result.product_sku == "SKU-001"


@pytest.mark.asyncio
async def test_get_transaction_by_id_not_found_raises_404(mock_conn, admin_user):
    transaction_repo = AsyncMock()
    transaction_repo.get_by_id_detailed.return_value = None

    service = _make_service(mock_conn, transaction_repo=transaction_repo)

    with pytest.raises(HTTPException) as exc:
        await service.get_transaction_by_id(999, admin_user)

    assert exc.value.status_code == 404


# ─── list_transactions ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_transactions_success(
    mock_conn, admin_user, sample_transaction_row
):
    from schemas.transaction_schema import TransactionResponse

    tx = TransactionResponse(**sample_transaction_row)
    transaction_repo = AsyncMock()
    transaction_repo.list_by_tenant.return_value = [tx]

    service = _make_service(mock_conn, transaction_repo=transaction_repo)
    filters = TransactionListRequest()

    result = await service.list_transactions(filters, admin_user)

    assert result.total == 1
    assert result.transactions[0].product_sku == "SKU-001"


@pytest.mark.asyncio
async def test_list_transactions_with_filters(mock_conn, admin_user):
    transaction_repo = AsyncMock()
    transaction_repo.list_by_tenant.return_value = []

    service = _make_service(mock_conn, transaction_repo=transaction_repo)
    filters = TransactionListRequest(
        type=TransactionType.IN, product_id=1, limit=10, offset=0
    )

    result = await service.list_transactions(filters, admin_user)

    transaction_repo.list_by_tenant.assert_called_once_with(
        tenant_id=admin_user.tenant_id,
        type=TransactionType.IN,
        warehouse_id=None,
        product_id=1,
        limit=10,
        offset=0,
    )
    assert result.total == 0
