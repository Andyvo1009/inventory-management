"""
Unit tests for TransactionRepository.

TransactionRepository is a concrete asyncpg implementation of
ITransactionRepository.  It converts raw asyncpg Records into typed domain
objects (InventoryTransaction) or Pydantic response models (TransactionResponse).

All tests replace the asyncpg connection with an AsyncMock so no database is
required.

Coverage map
─────────────────────────────────────────────────────────────────────────────
record
  • Returns InventoryTransaction built from INSERT RETURNING row             (1)
  • Uses explicit conn override when provided                                (1)

get_by_id
  • Returns InventoryTransaction when row exists                             (1)
  • Returns None when fetchrow returns None                                  (1)

list_by_tenant
  • Returns list[TransactionResponse], one per row                          (1)
  • Forwards type, warehouse_id, and product_id filter parameters           (1)
  • Returns empty list when fetch returns no rows                            (1)

get_by_id_detailed
  • Returns TransactionResponse when row exists                              (1)
  • Returns None when fetchrow returns None                                  (1)

list_by_operation
  • Returns list[TransactionResponse] for all rows of the operation         (1)
  • Returns empty list when fetch returns no rows                            (1)

list_inventory_by_operation
  • Returns list[InventoryTransaction] from raw transaction rows             (1)
  • Returns empty list when fetch returns no rows                            (1)

update_movement_status_by_operation
  • Calls conn.execute with the correct status value                         (1)

update_transaction_status
  • Returns InventoryTransaction with updated movement_status                (1)
  • Returns None when UPDATE matches no rows                                 (1)

update_transaction_quantity_and_note
  • Returns InventoryTransaction with updated quantity and note              (1)
  • Returns None when UPDATE matches no rows                                 (1)

check_all_transactions_completed
  • Returns True when fetchval returns True                                  (1)
  • Returns False when fetchval returns False                                (1)

check_any_transaction_failed
  • Returns True when fetchval returns True (at least one FAILED)           (1)
  • Returns False when fetchval returns False (none FAILED)                  (1)

get_transactions_by_type
  • Returns only rows matching the requested TransactionType                 (1)
  • Returns empty list when no rows match                                    (1)
─────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from models.models import InventoryTransaction, TransactionStatus, TransactionType
from repositories.transaction_repository import TransactionRepository
from schemas.transaction_schema import TransactionResponse


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _make_conn() -> AsyncMock:
    """Minimal asyncpg connection mock."""
    conn = AsyncMock()
    tx = AsyncMock()
    tx.__aenter__ = AsyncMock(return_value=None)
    tx.__aexit__ = AsyncMock(return_value=False)
    conn.transaction = MagicMock(return_value=tx)
    return conn


def _tx_row(
    tx_id: int = 1,
    op_id: int = 1,
    tx_type: str = "In",
    status: str = "Pending",
    qty: int = 10,
    product_id: int = 1,
    warehouse_id: int = 1,
) -> dict:
    """
    Dict mimicking a raw inventory_transactions row (as returned by record,
    get_by_id, list_inventory_by_operation, etc.).
    """
    return {
        "id": tx_id,
        "tenant_id": 1,
        "operation_id": op_id,
        "product_id": product_id,
        "user_id": 1,
        "warehouse_id": warehouse_id,
        "type": tx_type,
        "quantity": qty,
        "note": None,
        "timestamp": datetime(2026, 3, 1),
        "movement_status": status,
    }


def _detail_row(
    tx_id: int = 1,
    op_id: int = 1,
    tx_type: str = "In",
    status: str = "Completed",
) -> dict:
    """
    Dict mimicking the JOIN-rich row returned by list_by_tenant and
    list_by_operation (includes product, warehouse, user names).
    Includes operation_id and movement_status required by TransactionResponse.
    """
    return {
        "id": tx_id,
        "tenant_id": 1,
        "type": tx_type,
        "product_id": 1,
        "product_name": "Test Product",
        "product_sku": "SKU-001",
        "operation_id": op_id,
        "quantity": 10,
        "origin_warehouse_id": None,
        "origin_warehouse_name": None,
        "des_warehouse_id": 1,
        "des_warehouse_name": "Main Warehouse",
        "user_id": 1,
        "user_name": "Admin User",
        "note": None,
        "timestamp": datetime(2026, 3, 1),
        "movement_status": status,
    }


# ─── record ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_record_returns_inventory_transaction():
    """
    record inserts a transaction row and converts the RETURNING result into
    an InventoryTransaction dataclass with the correct field values.
    """
    conn = _make_conn()
    conn.fetchrow.return_value = _tx_row(tx_id=5, op_id=1, tx_type="In", status="Draft")

    repo = TransactionRepository(conn)
    result = await repo.record(
        tenant_id=1,
        operation_id=1,
        product_id=1,
        warehouse_id=1,
        type=TransactionType.IN,
        quantity=10,
        user_id=1,
        note=None,
    )

    assert isinstance(result, InventoryTransaction)
    assert result.id == 5
    assert result.type == TransactionType.IN
    assert result.movement_status == TransactionStatus.DRAFT
    conn.fetchrow.assert_awaited_once()


@pytest.mark.asyncio
async def test_record_uses_explicit_conn_override():
    """
    When a conn override is supplied, record must direct the INSERT to that
    connection instead of self._conn.
    """
    default_conn = _make_conn()
    explicit_conn = _make_conn()
    explicit_conn.fetchrow.return_value = _tx_row()

    repo = TransactionRepository(default_conn)
    await repo.record(
        tenant_id=1,
        operation_id=1,
        product_id=1,
        warehouse_id=1,
        type=TransactionType.IN,
        quantity=10,
        conn=explicit_conn,
    )

    explicit_conn.fetchrow.assert_awaited_once()
    default_conn.fetchrow.assert_not_awaited()


# ─── get_by_id ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_by_id_found():
    """
    get_by_id returns an InventoryTransaction when a matching row exists for
    the given tx_id and tenant_id.
    """
    conn = _make_conn()
    conn.fetchrow.return_value = _tx_row(tx_id=7, tx_type="Out", status="Completed")

    repo = TransactionRepository(conn)
    result = await repo.get_by_id(tx_id=7, tenant_id=1)

    assert result is not None
    assert result.id == 7
    assert result.type == TransactionType.OUT
    assert result.movement_status == TransactionStatus.COMPLETED


@pytest.mark.asyncio
async def test_get_by_id_not_found():
    """
    get_by_id returns None when fetchrow returns None (no matching transaction).
    """
    conn = _make_conn()
    conn.fetchrow.return_value = None

    repo = TransactionRepository(conn)
    result = await repo.get_by_id(tx_id=999, tenant_id=1)

    assert result is None


# ─── list_by_tenant ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_by_tenant_returns_transaction_responses():
    """
    list_by_tenant fetches JOIN-enriched rows and converts each to a
    TransactionResponse Pydantic model.
    """
    conn = _make_conn()
    conn.fetch.return_value = [_detail_row(tx_id=1), _detail_row(tx_id=2)]

    repo = TransactionRepository(conn)
    result = await repo.list_by_tenant(tenant_id=1)

    assert len(result) == 2
    assert all(isinstance(r, TransactionResponse) for r in result)
    assert result[0].id == 1
    assert result[1].id == 2


@pytest.mark.asyncio
async def test_list_by_tenant_forwards_filters():
    """
    list_by_tenant forwards type, warehouse_id, and product_id filter values
    as SQL bind parameters so the WHERE clause can apply them.
    """
    conn = _make_conn()
    conn.fetch.return_value = [_detail_row()]

    repo = TransactionRepository(conn)
    await repo.list_by_tenant(
        tenant_id=1,
        type=TransactionType.IN,
        warehouse_id=3,
        product_id=7,
        limit=25,
        offset=10,
    )

    args = conn.fetch.call_args[0]
    assert "In" in args       # type.value
    assert 3 in args          # warehouse_id
    assert 7 in args          # product_id
    assert 25 in args         # limit
    assert 10 in args         # offset


@pytest.mark.asyncio
async def test_list_by_tenant_empty():
    """
    list_by_tenant returns an empty list when there are no matching transactions.
    """
    conn = _make_conn()
    conn.fetch.return_value = []

    repo = TransactionRepository(conn)
    result = await repo.list_by_tenant(tenant_id=1)

    assert result == []


# ─── get_by_id_detailed ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_by_id_detailed_found():
    """
    get_by_id_detailed returns a TransactionResponse (Pydantic model) built
    from the JOIN-enriched single-row query result.
    """
    conn = _make_conn()
    conn.fetchrow.return_value = _detail_row(tx_id=4, tx_type="Out", status="Completed")

    repo = TransactionRepository(conn)
    result = await repo.get_by_id_detailed(tx_id=4, tenant_id=1)

    assert result is not None
    assert isinstance(result, TransactionResponse)
    assert result.id == 4
    assert result.type == TransactionType.OUT


@pytest.mark.asyncio
async def test_get_by_id_detailed_not_found():
    """
    get_by_id_detailed returns None when fetchrow returns None.
    """
    conn = _make_conn()
    conn.fetchrow.return_value = None

    repo = TransactionRepository(conn)
    result = await repo.get_by_id_detailed(tx_id=999, tenant_id=1)

    assert result is None


# ─── list_by_operation ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_by_operation_returns_transaction_responses():
    """
    list_by_operation returns all JOIN-enriched TransactionResponse objects
    that belong to the specified operation.
    """
    conn = _make_conn()
    conn.fetch.return_value = [
        _detail_row(tx_id=10, op_id=5),
        _detail_row(tx_id=11, op_id=5),
    ]

    repo = TransactionRepository(conn)
    result = await repo.list_by_operation(operation_id=5, tenant_id=1)

    assert len(result) == 2
    assert all(isinstance(r, TransactionResponse) for r in result)


@pytest.mark.asyncio
async def test_list_by_operation_empty():
    """
    list_by_operation returns an empty list when the operation has no
    transaction lines.
    """
    conn = _make_conn()
    conn.fetch.return_value = []

    repo = TransactionRepository(conn)
    result = await repo.list_by_operation(operation_id=99, tenant_id=1)

    assert result == []


# ─── list_inventory_by_operation ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_inventory_by_operation_returns_domain_objects():
    """
    list_inventory_by_operation returns raw InventoryTransaction domain objects
    (not TransactionResponse).  This is used internally by OperationService for
    stock-mutation logic.
    """
    conn = _make_conn()
    conn.fetch.return_value = [
        _tx_row(tx_id=1, tx_type="Out", status="Pending"),
        _tx_row(tx_id=2, tx_type="In", status="Pending"),
    ]

    repo = TransactionRepository(conn)
    result = await repo.list_inventory_by_operation(operation_id=1, tenant_id=1)

    assert len(result) == 2
    assert all(isinstance(r, InventoryTransaction) for r in result)
    assert result[0].type == TransactionType.OUT
    assert result[1].type == TransactionType.IN


@pytest.mark.asyncio
async def test_list_inventory_by_operation_empty():
    """
    list_inventory_by_operation returns an empty list when the operation has
    no transaction lines.
    """
    conn = _make_conn()
    conn.fetch.return_value = []

    repo = TransactionRepository(conn)
    result = await repo.list_inventory_by_operation(operation_id=99, tenant_id=1)

    assert result == []


# ─── update_movement_status_by_operation ─────────────────────────────────────


@pytest.mark.asyncio
async def test_update_movement_status_by_operation_calls_execute():
    """
    update_movement_status_by_operation issues a bulk UPDATE via conn.execute
    and passes the correct movement_status enum value as a bind parameter.
    """
    conn = _make_conn()
    conn.execute.return_value = "UPDATE 3"

    repo = TransactionRepository(conn)
    await repo.update_movement_status_by_operation(
        operation_id=1,
        tenant_id=1,
        movement_status=TransactionStatus.PENDING,
    )

    conn.execute.assert_awaited_once()
    args = conn.execute.call_args[0]
    assert "Pending" in args  # movement_status.value passed as a bind param


# ─── update_transaction_status ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_transaction_status_returns_updated_transaction():
    """
    update_transaction_status issues UPDATE … RETURNING and converts the row
    into an InventoryTransaction with the new movement_status.
    """
    conn = _make_conn()
    conn.fetchrow.return_value = _tx_row(tx_id=1, status="Completed")

    repo = TransactionRepository(conn)
    result = await repo.update_transaction_status(
        transaction_id=1,
        tenant_id=1,
        movement_status=TransactionStatus.COMPLETED,
    )

    assert result is not None
    assert result.movement_status == TransactionStatus.COMPLETED
    conn.fetchrow.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_transaction_status_not_found_returns_none():
    """
    update_transaction_status returns None when the UPDATE matches no rows
    (the transaction does not exist in the tenant's scope).
    """
    conn = _make_conn()
    conn.fetchrow.return_value = None

    repo = TransactionRepository(conn)
    result = await repo.update_transaction_status(
        transaction_id=999,
        tenant_id=1,
        movement_status=TransactionStatus.FAILED,
    )

    assert result is None


# ─── update_transaction_quantity_and_note ────────────────────────────────────


@pytest.mark.asyncio
async def test_update_transaction_quantity_and_note_returns_updated():
    """
    update_transaction_quantity_and_note issues UPDATE … RETURNING and returns
    an InventoryTransaction with the updated quantity and note values.
    """
    updated_row = {**_tx_row(tx_id=1, qty=6), "note": "Partial receipt"}
    conn = _make_conn()
    conn.fetchrow.return_value = updated_row

    repo = TransactionRepository(conn)
    result = await repo.update_transaction_quantity_and_note(
        transaction_id=1,
        tenant_id=1,
        quantity=6,
        note="Partial receipt",
    )

    assert result is not None
    assert result.quantity == 6
    assert result.note == "Partial receipt"


@pytest.mark.asyncio
async def test_update_transaction_quantity_and_note_not_found_returns_none():
    """
    update_transaction_quantity_and_note returns None when the UPDATE matches
    no rows.
    """
    conn = _make_conn()
    conn.fetchrow.return_value = None

    repo = TransactionRepository(conn)
    result = await repo.update_transaction_quantity_and_note(
        transaction_id=999,
        tenant_id=1,
        quantity=5,
        note=None,
    )

    assert result is None


# ─── check_all_transactions_completed ────────────────────────────────────────


@pytest.mark.asyncio
async def test_check_all_transactions_completed_true():
    """
    check_all_transactions_completed returns True when every transaction in
    the operation is in COMPLETED state (DB COUNT(*) = 0 of non-completed).
    """
    conn = _make_conn()
    conn.fetchval.return_value = True

    repo = TransactionRepository(conn)
    result = await repo.check_all_transactions_completed(
        operation_id=1, tenant_id=1
    )

    assert result is True
    conn.fetchval.assert_awaited_once()


@pytest.mark.asyncio
async def test_check_all_transactions_completed_false():
    """
    check_all_transactions_completed returns False when at least one
    transaction is not yet completed.
    """
    conn = _make_conn()
    conn.fetchval.return_value = False

    repo = TransactionRepository(conn)
    result = await repo.check_all_transactions_completed(
        operation_id=1, tenant_id=1
    )

    assert result is False


# ─── check_any_transaction_failed ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_check_any_transaction_failed_true():
    """
    check_any_transaction_failed returns True when at least one transaction
    in the operation has movement_status = FAILED.
    """
    conn = _make_conn()
    conn.fetchval.return_value = True

    repo = TransactionRepository(conn)
    result = await repo.check_any_transaction_failed(
        operation_id=1, tenant_id=1
    )

    assert result is True
    conn.fetchval.assert_awaited_once()


@pytest.mark.asyncio
async def test_check_any_transaction_failed_false():
    """
    check_any_transaction_failed returns False when no transaction in the
    operation has failed.
    """
    conn = _make_conn()
    conn.fetchval.return_value = False

    repo = TransactionRepository(conn)
    result = await repo.check_any_transaction_failed(
        operation_id=1, tenant_id=1
    )

    assert result is False


# ─── get_transactions_by_type ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_transactions_by_type_returns_matching_rows():
    """
    get_transactions_by_type returns only InventoryTransaction objects whose
    type matches the requested TransactionType.  The repository passes the
    enum value as a bind parameter; the DB applies the filter.
    """
    conn = _make_conn()
    conn.fetch.return_value = [
        _tx_row(tx_id=1, tx_type="Out", status="Completed"),
        _tx_row(tx_id=2, tx_type="Out", status="Completed"),
    ]

    repo = TransactionRepository(conn)
    result = await repo.get_transactions_by_type(
        operation_id=1,
        tenant_id=1,
        transaction_type=TransactionType.OUT,
    )

    assert len(result) == 2
    assert all(r.type == TransactionType.OUT for r in result)
    # Verify the enum value was passed as a bind parameter
    args = conn.fetch.call_args[0]
    assert "Out" in args


@pytest.mark.asyncio
async def test_get_transactions_by_type_empty():
    """
    get_transactions_by_type returns an empty list when no transactions of
    the requested type exist for the operation.
    """
    conn = _make_conn()
    conn.fetch.return_value = []

    repo = TransactionRepository(conn)
    result = await repo.get_transactions_by_type(
        operation_id=1,
        tenant_id=1,
        transaction_type=TransactionType.IN,
    )

    assert result == []
