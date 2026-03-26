"""
Unit tests for OperationRepository.

OperationRepository is a thin asyncpg wrapper; every method either calls
conn.fetchrow / conn.fetch / conn.execute and maps rows to domain objects.
All tests replace the asyncpg connection with an AsyncMock so no database is
required.

Coverage map
─────────────────────────────────────────────────────────────────────────────
create
  • Returns an InventoryOperation built from the INSERT RETURNING row       (1)
  • Passes an explicit conn override to the query                           (1)

get_by_id
  • Returns InventoryOperation when row exists                              (1)
  • Returns None when fetchrow returns None                                 (1)

get_by_id_for_update
  • Returns InventoryOperation (uses FOR UPDATE variant of the query)       (1)
  • Returns None when fetchrow returns None                                 (1)

update_status
  • Returns updated InventoryOperation with new status                      (1)
  • Returns None when the operation does not exist                          (1)

list_by_tenant
  • Returns list[dict] with one entry per row                               (1)
  • Passes operation_type and status filter values to the query             (1)
  • Returns empty list when fetch returns no rows                           (1)

get_detailed
  • Returns a dict with header fields and an 'items' list                   (1)
  • Returns None when the header fetchrow returns None                      (1)
  • items list contains one dict per item row                               (1)
─────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from models.models import InventoryOperation, OperationStatus, OperationType
from repositories.operation_repository import OperationRepository


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _make_conn() -> AsyncMock:
    """Minimal asyncpg connection mock with transaction support."""
    conn = AsyncMock()
    tx = AsyncMock()
    tx.__aenter__ = AsyncMock(return_value=None)
    tx.__aexit__ = AsyncMock(return_value=False)
    conn.transaction = MagicMock(return_value=tx)
    return conn


def _op_row(
    op_id: int = 1,
    op_type: str = "Purchase",
    status: str = "Pending",
    source_wh: int | None = None,
    dest_wh: int | None = 1,
) -> dict:
    """A dict that mimics an asyncpg Record for an inventory_operations row."""
    return {
        "id": op_id,
        "tenant_id": 1,
        "user_id": 1,
        "operation_type": op_type,
        "status": status,
        "source_warehouse_id": source_wh,
        "destination_warehouse_id": dest_wh,
        "reference_code": None,
        "note": None,
        "created_at": datetime(2026, 3, 1),
        "updated_at": datetime(2026, 3, 1),
    }


def _list_row(op_id: int = 1, op_type: str = "Purchase", status: str = "Pending") -> dict:
    """A dict mimicking a row from the list_by_tenant JOIN query."""
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
    }


def _header_row(op_id: int = 1) -> dict:
    """A dict mimicking the header fetchrow result from get_detailed."""
    return {
        "id": op_id,
        "tenant_id": 1,
        "operation_type": "Purchase",
        "status": "Completed",
        "source_warehouse_id": None,
        "source_warehouse_name": None,
        "destination_warehouse_id": 1,
        "destination_warehouse_name": "Main Warehouse",
        "user_id": 1,
        "user_name": "Admin User",
        "reference_code": None,
        "note": None,
        "created_at": datetime(2026, 3, 1),
        "updated_at": datetime(2026, 3, 1),
    }


def _item_row(tx_id: int = 1, op_id: int = 1) -> dict:
    """A dict mimicking a single transaction-line row from get_detailed."""
    return {
        "id": tx_id,
        "operation_id": op_id,
        "product_id": 1,
        "product_name": "Test Product",
        "product_sku": "SKU-001",
        "type": "In",
        "warehouse_id": 1,
        "warehouse_name": "Main Warehouse",
        "quantity": 10,
        "movement_status": "Completed",
    }


# ─── create ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_returns_inventory_operation():
    """
    create calls INSERT … RETURNING and converts the returned row into an
    InventoryOperation dataclass with correct field values.
    """
    conn = _make_conn()
    conn.fetchrow.return_value = _op_row(op_id=1, op_type="Purchase", status="Pending")

    repo = OperationRepository(conn)
    result = await repo.create(
        tenant_id=1,
        operation_type=OperationType.PURCHASE,
        status=OperationStatus.PENDING,
        source_warehouse_id=None,
        destination_warehouse_id=1,
        reference_code=None,
        user_id=1,
        note=None,
    )

    assert isinstance(result, InventoryOperation)
    assert result.id == 1
    assert result.operation_type == OperationType.PURCHASE
    assert result.status == OperationStatus.PENDING
    conn.fetchrow.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_uses_explicit_conn_override():
    """
    When an explicit conn keyword argument is passed, create must use that
    connection for the INSERT query rather than self._conn.
    """
    default_conn = _make_conn()
    explicit_conn = _make_conn()
    explicit_conn.fetchrow.return_value = _op_row()

    repo = OperationRepository(default_conn)
    await repo.create(
        tenant_id=1,
        operation_type=OperationType.PURCHASE,
        status=OperationStatus.PENDING,
        source_warehouse_id=None,
        destination_warehouse_id=None,
        reference_code=None,
        user_id=1,
        note=None,
        conn=explicit_conn,
    )

    explicit_conn.fetchrow.assert_awaited_once()
    default_conn.fetchrow.assert_not_awaited()


# ─── get_by_id ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_by_id_found():
    """
    get_by_id returns an InventoryOperation when the operation exists
    in the tenant's scope.
    """
    conn = _make_conn()
    conn.fetchrow.return_value = _op_row(op_id=3, op_type="Sale", status="Completed")

    repo = OperationRepository(conn)
    result = await repo.get_by_id(operation_id=3, tenant_id=1)

    assert result is not None
    assert result.id == 3
    assert result.operation_type == OperationType.SALE
    assert result.status == OperationStatus.COMPLETED


@pytest.mark.asyncio
async def test_get_by_id_not_found():
    """
    get_by_id returns None when fetchrow returns None (no matching row).
    """
    conn = _make_conn()
    conn.fetchrow.return_value = None

    repo = OperationRepository(conn)
    result = await repo.get_by_id(operation_id=999, tenant_id=1)

    assert result is None


# ─── get_by_id_for_update ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_by_id_for_update_found():
    """
    get_by_id_for_update returns the InventoryOperation when the row exists.
    This method appends FOR UPDATE to the query for pessimistic locking.
    """
    conn = _make_conn()
    conn.fetchrow.return_value = _op_row(op_id=2, status="Pending")

    repo = OperationRepository(conn)
    result = await repo.get_by_id_for_update(operation_id=2, tenant_id=1)

    assert result is not None
    assert result.id == 2
    conn.fetchrow.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_by_id_for_update_not_found():
    """
    get_by_id_for_update returns None when no matching row exists.
    The FOR UPDATE clause still applies; the query simply returns no row.
    """
    conn = _make_conn()
    conn.fetchrow.return_value = None

    repo = OperationRepository(conn)
    result = await repo.get_by_id_for_update(operation_id=999, tenant_id=1)

    assert result is None


# ─── update_status ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_status_returns_updated_operation():
    """
    update_status executes UPDATE … RETURNING and returns an InventoryOperation
    with the new status reflected in the dataclass fields.
    """
    conn = _make_conn()
    conn.fetchrow.return_value = _op_row(op_id=1, status="Completed")

    repo = OperationRepository(conn)
    result = await repo.update_status(
        operation_id=1, tenant_id=1, status=OperationStatus.COMPLETED
    )

    assert result is not None
    assert result.status == OperationStatus.COMPLETED
    conn.fetchrow.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_status_not_found_returns_none():
    """
    update_status returns None when the UPDATE matches no rows (the operation
    does not exist in the tenant's scope).
    """
    conn = _make_conn()
    conn.fetchrow.return_value = None

    repo = OperationRepository(conn)
    result = await repo.update_status(
        operation_id=999, tenant_id=1, status=OperationStatus.CANCELLED
    )

    assert result is None


# ─── list_by_tenant ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_by_tenant_returns_list_of_dicts():
    """
    list_by_tenant converts each asyncpg Record to a plain dict and returns
    the full list.  One dict per operation row.
    """
    conn = _make_conn()
    conn.fetch.return_value = [_list_row(op_id=1), _list_row(op_id=2)]

    repo = OperationRepository(conn)
    result = await repo.list_by_tenant(
        tenant_id=1,
        operation_type=None,
        status=None,
        warehouse_id=None,
        limit=50,
        offset=0,
    )

    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[1]["id"] == 2


@pytest.mark.asyncio
async def test_list_by_tenant_passes_filter_values():
    """
    list_by_tenant forwards the operation_type and status enum values (as
    strings) to the parameterised query.  The correct positional arguments
    must be passed to conn.fetch.
    """
    conn = _make_conn()
    conn.fetch.return_value = [_list_row()]

    repo = OperationRepository(conn)
    await repo.list_by_tenant(
        tenant_id=1,
        operation_type=OperationType.PURCHASE,
        status=OperationStatus.PENDING,
        warehouse_id=None,
        limit=10,
        offset=0,
    )

    args = conn.fetch.call_args[0]  # positional args passed to fetch
    # args[0] is the SQL string; remaining are bind parameters
    assert "Purchase" in args  # operation_type.value
    assert "Pending" in args   # status.value


@pytest.mark.asyncio
async def test_list_by_tenant_empty():
    """
    list_by_tenant returns an empty list when the tenant has no operations
    matching the given criteria.
    """
    conn = _make_conn()
    conn.fetch.return_value = []

    repo = OperationRepository(conn)
    result = await repo.list_by_tenant(
        tenant_id=1,
        operation_type=None,
        status=None,
        warehouse_id=None,
        limit=50,
        offset=0,
    )

    assert result == []


# ─── get_detailed ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_detailed_found_returns_dict_with_items():
    """
    get_detailed fetches the operation header via fetchrow and the transaction
    items via fetch, then merges them into a single dict with an 'items' key.
    """
    conn = _make_conn()
    conn.fetchrow.return_value = _header_row(op_id=1)
    conn.fetch.return_value = [_item_row(tx_id=10, op_id=1)]

    repo = OperationRepository(conn)
    result = await repo.get_detailed(operation_id=1, tenant_id=1)

    assert result is not None
    assert result["id"] == 1
    assert "items" in result
    assert len(result["items"]) == 1
    assert result["items"][0]["id"] == 10


@pytest.mark.asyncio
async def test_get_detailed_not_found_returns_none():
    """
    get_detailed returns None when the header fetchrow returns None,
    meaning the operation does not exist in the caller's tenant.
    """
    conn = _make_conn()
    conn.fetchrow.return_value = None

    repo = OperationRepository(conn)
    result = await repo.get_detailed(operation_id=999, tenant_id=1)

    assert result is None


@pytest.mark.asyncio
async def test_get_detailed_no_items_returns_empty_items_list():
    """
    get_detailed returns an 'items' list of [] when the operation has no
    associated transaction lines.
    """
    conn = _make_conn()
    conn.fetchrow.return_value = _header_row(op_id=5)
    conn.fetch.return_value = []  # no item rows

    repo = OperationRepository(conn)
    result = await repo.get_detailed(operation_id=5, tenant_id=1)

    assert result is not None
    assert result["items"] == []
