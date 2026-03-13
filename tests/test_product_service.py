"""
Unit tests for ProductService.

Covers: create, get by ID, list, update, and delete — including role
enforcement and not-found paths.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from models.models import Product, UserRole
from schemas.product_schema import (
    ProductCreateRequest,
    ProductListRequest,
    ProductUpdateRequest,
)
from services.product_service import ProductService


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _make_service(mock_conn, product_repo=None) -> ProductService:
    repo = product_repo or AsyncMock()
    return ProductService(mock_conn, product_repo=repo)


# ─── create_product ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_product_admin_success(mock_conn, admin_user, sample_product):
    repo = AsyncMock()
    repo.get_by_sku.return_value = None
    repo.create.return_value = sample_product

    service = _make_service(mock_conn, repo)
    data = ProductCreateRequest(
        sku="SKU-001",
        name="Test Product",
        description="Desc",
        category_id=1,
        reorder_point=5,
    )

    result = await service.create_product(data, admin_user)

    assert result.sku == "SKU-001"
    assert result.name == "Test Product"
    repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_product_staff_raises_403(mock_conn, staff_user):
    service = _make_service(mock_conn)
    data = ProductCreateRequest(sku="SKU-X", name="Product X")

    with pytest.raises(HTTPException) as exc:
        await service.create_product(data, staff_user)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_create_product_duplicate_sku_raises_400(
    mock_conn, admin_user, sample_product
):
    repo = AsyncMock()
    repo.get_by_sku.return_value = sample_product  # already exists

    service = _make_service(mock_conn, repo)
    data = ProductCreateRequest(sku="SKU-001", name="Duplicate")

    with pytest.raises(HTTPException) as exc:
        await service.create_product(data, admin_user)

    assert exc.value.status_code == 400
    assert "SKU-001" in exc.value.detail


# ─── get_product_by_id ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_product_by_id_success(mock_conn, admin_user, sample_product):
    from schemas.product_schema import ProductResponse

    repo = AsyncMock()
    repo.get_by_id.return_value = ProductResponse.from_product(sample_product)

    service = _make_service(mock_conn, repo)
    result = await service.get_product_by_id(1, admin_user)

    assert result.id == 1
    assert result.sku == "SKU-001"


@pytest.mark.asyncio
async def test_get_product_by_id_not_found_raises_404(mock_conn, admin_user):
    repo = AsyncMock()
    repo.get_by_id.return_value = None

    service = _make_service(mock_conn, repo)

    with pytest.raises(HTTPException) as exc:
        await service.get_product_by_id(999, admin_user)

    assert exc.value.status_code == 404


# ─── list_products ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_products_success(mock_conn, admin_user, sample_product):
    from schemas.product_schema import ProductResponse

    repo = AsyncMock()
    repo.list_by_tenant.return_value = [ProductResponse.from_product(sample_product)]

    service = _make_service(mock_conn, repo)
    filters = ProductListRequest()

    result = await service.list_products(filters, admin_user)

    assert result.total == 1
    assert len(result.products) == 1


@pytest.mark.asyncio
async def test_list_products_empty(mock_conn, staff_user):
    repo = AsyncMock()
    repo.list_by_tenant.return_value = []

    service = _make_service(mock_conn, repo)
    filters = ProductListRequest()

    result = await service.list_products(filters, staff_user)

    assert result.total == 0
    assert result.products == []


@pytest.mark.asyncio
async def test_list_products_with_filters(mock_conn, admin_user, sample_product):
    from schemas.product_schema import ProductResponse

    repo = AsyncMock()
    repo.list_by_tenant.return_value = [ProductResponse.from_product(sample_product)]

    service = _make_service(mock_conn, repo)
    filters = ProductListRequest(category_id=1, search="Test", limit=10, offset=0)

    result = await service.list_products(filters, admin_user)

    repo.list_by_tenant.assert_called_once_with(
        tenant_id=admin_user.tenant_id,
        category_id=1,
        search="Test",
        limit=10,
        offset=0,
    )
    assert result.limit == 10
    assert result.offset == 0


# ─── update_product ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_product_admin_success(mock_conn, admin_user, sample_product):
    repo = AsyncMock()
    updated = Product(
        id=1,
        tenant_id=1,
        category_id=1,
        sku="SKU-001",
        name="Updated Name",
        description="New desc",
        reorder_point=20,
    )
    repo.update.return_value = updated

    service = _make_service(mock_conn, repo)
    data = ProductUpdateRequest(name="Updated Name", reorder_point=20)

    result = await service.update_product(1, data, admin_user)

    assert result.name == "Updated Name"
    assert result.reorder_point == 20


@pytest.mark.asyncio
async def test_update_product_staff_raises_403(mock_conn, staff_user):
    service = _make_service(mock_conn)
    data = ProductUpdateRequest(name="New")

    with pytest.raises(HTTPException) as exc:
        await service.update_product(1, data, staff_user)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_update_product_not_found_raises_404(mock_conn, admin_user):
    repo = AsyncMock()
    repo.update.return_value = None

    service = _make_service(mock_conn, repo)
    data = ProductUpdateRequest(name="X")

    with pytest.raises(HTTPException) as exc:
        await service.update_product(999, data, admin_user)

    assert exc.value.status_code == 404


# ─── delete_product ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_product_admin_success(mock_conn, admin_user):
    repo = AsyncMock()
    repo.delete.return_value = True

    service = _make_service(mock_conn, repo)
    # Should not raise
    await service.delete_product(1, admin_user)
    repo.delete.assert_called_once()


@pytest.mark.asyncio
async def test_delete_product_staff_raises_403(mock_conn, staff_user):
    service = _make_service(mock_conn)

    with pytest.raises(HTTPException) as exc:
        await service.delete_product(1, staff_user)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_delete_product_not_found_raises_404(mock_conn, admin_user):
    repo = AsyncMock()
    repo.delete.return_value = False

    service = _make_service(mock_conn, repo)

    with pytest.raises(HTTPException) as exc:
        await service.delete_product(999, admin_user)

    assert exc.value.status_code == 404
