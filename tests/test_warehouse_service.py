"""
Unit tests for WarehouseService.

Covers: create, get detail (with mocked SQL), list (with mocked SQL),
update, and delete — including role enforcement and not-found paths.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from models.models import Warehouse
from schemas.warehouse_schema import WarehouseCreateRequest, WarehouseUpdateRequest
from services.warehouse_service import WarehouseService


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _make_service(
    mock_conn,
    warehouse_repo=None,
    stock_repo=None,
) -> WarehouseService:
    return WarehouseService(
        mock_conn,
        warehouse_repo=warehouse_repo or AsyncMock(),
        stock_repo=stock_repo or AsyncMock(),
    )


# ─── create_warehouse ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_warehouse_admin_success(
    mock_conn, admin_user, sample_warehouse
):
    repo = AsyncMock()
    repo.create.return_value = sample_warehouse

    service = _make_service(mock_conn, warehouse_repo=repo)
    data = WarehouseCreateRequest(name="Main Warehouse", location="Building A")

    result = await service.create_warehouse(data, admin_user)

    assert result.name == "Main Warehouse"
    assert result.location == "Building A"
    repo.create.assert_called_once_with(
        tenant_id=admin_user.tenant_id,
        name="Main Warehouse",
        location="Building A",
    )


@pytest.mark.asyncio
async def test_create_warehouse_staff_raises_403(mock_conn, staff_user):
    service = _make_service(mock_conn)
    data = WarehouseCreateRequest(name="WH", location=None)

    with pytest.raises(HTTPException) as exc:
        await service.create_warehouse(data, staff_user)

    assert exc.value.status_code == 403


# ─── get_warehouse_by_id ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_warehouse_by_id_success(mock_conn, admin_user, sample_warehouse):
    repo = AsyncMock()
    repo.get_by_id.return_value = sample_warehouse

    # Mock the SQL fetch for stock rows
    mock_conn.fetch.return_value = [
        {
            "product_id": 1,
            "sku": "SKU-001",
            "product_name": "Test Product",
            "category_name": "Electronics",
            "quantity": 50,
        }
    ]

    service = _make_service(mock_conn, warehouse_repo=repo)
    result = await service.get_warehouse_by_id(1, admin_user)

    assert result.id == 1
    assert result.total_unique_products == 1
    assert result.total_stock == 50
    assert result.products[0].sku == "SKU-001"


@pytest.mark.asyncio
async def test_get_warehouse_by_id_not_found_raises_404(mock_conn, admin_user):
    repo = AsyncMock()
    repo.get_by_id.return_value = None

    service = _make_service(mock_conn, warehouse_repo=repo)

    with pytest.raises(HTTPException) as exc:
        await service.get_warehouse_by_id(999, admin_user)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_warehouse_by_id_empty_stock(mock_conn, admin_user, sample_warehouse):
    repo = AsyncMock()
    repo.get_by_id.return_value = sample_warehouse
    mock_conn.fetch.return_value = []  # no stock

    service = _make_service(mock_conn, warehouse_repo=repo)
    result = await service.get_warehouse_by_id(1, admin_user)

    assert result.total_unique_products == 0
    assert result.total_stock == 0
    assert result.products == []


# ─── list_warehouses ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_warehouses_success(
    mock_conn, admin_user, sample_warehouse, sample_warehouse_b
):
    repo = AsyncMock()
    repo.list_by_tenant.return_value = [sample_warehouse, sample_warehouse_b]

    # fetchrow called once per warehouse for the stock summary
    mock_conn.fetchrow.side_effect = [
        {"total_unique_products": 3, "total_stock": 150},
        {"total_unique_products": 1, "total_stock": 40},
    ]

    service = _make_service(mock_conn, warehouse_repo=repo)
    result = await service.list_warehouses(admin_user)

    assert result.total == 2
    assert result.warehouses[0].total_stock == 150
    assert result.warehouses[1].total_stock == 40


@pytest.mark.asyncio
async def test_list_warehouses_empty(mock_conn, staff_user):
    repo = AsyncMock()
    repo.list_by_tenant.return_value = []

    service = _make_service(mock_conn, warehouse_repo=repo)
    result = await service.list_warehouses(staff_user)

    assert result.total == 0
    assert result.warehouses == []


# ─── update_warehouse ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_warehouse_admin_success(
    mock_conn, admin_user, sample_warehouse
):
    updated = Warehouse(
        id=1, tenant_id=1, name="Updated Warehouse", location="Building C"
    )
    repo = AsyncMock()
    repo.update.return_value = updated

    service = _make_service(mock_conn, warehouse_repo=repo)
    data = WarehouseUpdateRequest(name="Updated Warehouse", location="Building C")

    result = await service.update_warehouse(1, data, admin_user)

    assert result.name == "Updated Warehouse"
    assert result.location == "Building C"


@pytest.mark.asyncio
async def test_update_warehouse_staff_raises_403(mock_conn, staff_user):
    service = _make_service(mock_conn)
    data = WarehouseUpdateRequest(name="New Name")

    with pytest.raises(HTTPException) as exc:
        await service.update_warehouse(1, data, staff_user)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_update_warehouse_not_found_raises_404(mock_conn, admin_user):
    repo = AsyncMock()
    repo.update.return_value = None

    service = _make_service(mock_conn, warehouse_repo=repo)
    data = WarehouseUpdateRequest(name="X")

    with pytest.raises(HTTPException) as exc:
        await service.update_warehouse(999, data, admin_user)

    assert exc.value.status_code == 404


# ─── delete_warehouse ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_warehouse_admin_success(mock_conn, admin_user):
    repo = AsyncMock()
    repo.delete.return_value = True

    service = _make_service(mock_conn, warehouse_repo=repo)
    await service.delete_warehouse(1, admin_user)

    repo.delete.assert_called_once_with(
        warehouse_id=1, tenant_id=admin_user.tenant_id
    )


@pytest.mark.asyncio
async def test_delete_warehouse_staff_raises_403(mock_conn, staff_user):
    service = _make_service(mock_conn)

    with pytest.raises(HTTPException) as exc:
        await service.delete_warehouse(1, staff_user)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_delete_warehouse_not_found_raises_404(mock_conn, admin_user):
    repo = AsyncMock()
    repo.delete.return_value = False

    service = _make_service(mock_conn, warehouse_repo=repo)

    with pytest.raises(HTTPException) as exc:
        await service.delete_warehouse(999, admin_user)

    assert exc.value.status_code == 404
