"""
Unit tests for CategoryService.

Covers: create, get by ID, list (all / roots / children), update
(including circular-reference guard), and delete.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from models.models import Category
from schemas.category_schema import CategoryCreateRequest, CategoryUpdateRequest
from services.category_service import CategoryService


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _make_service(mock_conn, category_repo=None) -> CategoryService:
    repo = category_repo or AsyncMock()
    return CategoryService(mock_conn, category_repo=repo)


# ─── create_category ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_category_admin_success(
    mock_conn, admin_user, sample_category
):
    repo = AsyncMock()
    repo.create.return_value = sample_category

    service = _make_service(mock_conn, repo)
    data = CategoryCreateRequest(name="Electronics")

    result = await service.create_category(data, admin_user)

    assert result.name == "Electronics"
    assert result.tenant_id == 1
    repo.create.assert_called_once_with(
        tenant_id=admin_user.tenant_id,
        name="Electronics",
        parent_id=None,
    )


@pytest.mark.asyncio
async def test_create_category_staff_raises_403(mock_conn, staff_user):
    service = _make_service(mock_conn)
    data = CategoryCreateRequest(name="Phones")

    with pytest.raises(HTTPException) as exc:
        await service.create_category(data, staff_user)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_create_category_with_valid_parent(
    mock_conn, admin_user, sample_category, sample_child_category
):
    repo = AsyncMock()
    repo.get_by_id.return_value = sample_category  # parent exists
    repo.create.return_value = sample_child_category

    service = _make_service(mock_conn, repo)
    data = CategoryCreateRequest(name="Laptops", parent_id=1)

    result = await service.create_category(data, admin_user)

    assert result.parent_id == 1
    repo.get_by_id.assert_called_once_with(
        category_id=1, tenant_id=admin_user.tenant_id
    )


@pytest.mark.asyncio
async def test_create_category_parent_not_found_raises_404(mock_conn, admin_user):
    repo = AsyncMock()
    repo.get_by_id.return_value = None  # parent missing

    service = _make_service(mock_conn, repo)
    data = CategoryCreateRequest(name="Laptops", parent_id=99)

    with pytest.raises(HTTPException) as exc:
        await service.create_category(data, admin_user)

    assert exc.value.status_code == 404
    assert "99" in exc.value.detail


# ─── get_category_by_id ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_category_by_id_success(mock_conn, admin_user, sample_category):
    repo = AsyncMock()
    repo.get_by_id.return_value = sample_category

    service = _make_service(mock_conn, repo)
    result = await service.get_category_by_id(1, admin_user)

    assert result.id == 1
    assert result.name == "Electronics"


@pytest.mark.asyncio
async def test_get_category_by_id_not_found_raises_404(mock_conn, staff_user):
    repo = AsyncMock()
    repo.get_by_id.return_value = None

    service = _make_service(mock_conn, repo)

    with pytest.raises(HTTPException) as exc:
        await service.get_category_by_id(999, staff_user)

    assert exc.value.status_code == 404


# ─── list_categories ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_all_categories(mock_conn, admin_user, sample_category):
    repo = AsyncMock()
    repo.list_by_tenant.return_value = [sample_category]

    service = _make_service(mock_conn, repo)
    result = await service.list_categories(admin_user)

    assert result.total == 1
    repo.list_by_tenant.assert_called_once_with(tenant_id=admin_user.tenant_id)


@pytest.mark.asyncio
async def test_list_root_categories(mock_conn, admin_user, sample_category):
    repo = AsyncMock()
    repo.list_roots.return_value = [sample_category]

    service = _make_service(mock_conn, repo)
    result = await service.list_categories(admin_user, roots_only=True)

    assert result.total == 1
    repo.list_roots.assert_called_once_with(tenant_id=admin_user.tenant_id)


@pytest.mark.asyncio
async def test_list_children_categories(
    mock_conn, admin_user, sample_child_category
):
    repo = AsyncMock()
    repo.list_children.return_value = [sample_child_category]

    service = _make_service(mock_conn, repo)
    result = await service.list_categories(admin_user, parent_id=1)

    assert result.total == 1
    assert result.categories[0].parent_id == 1
    repo.list_children.assert_called_once_with(
        parent_id=1, tenant_id=admin_user.tenant_id
    )


# ─── update_category ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_category_admin_success(mock_conn, admin_user, sample_category):
    updated = Category(id=1, tenant_id=1, name="Consumer Electronics", parent_id=None)
    repo = AsyncMock()
    repo.get_by_id.return_value = sample_category  # exists
    repo.update.return_value = updated

    service = _make_service(mock_conn, repo)
    data = CategoryUpdateRequest(name="Consumer Electronics")

    result = await service.update_category(1, data, admin_user)

    assert result.name == "Consumer Electronics"


@pytest.mark.asyncio
async def test_update_category_staff_raises_403(mock_conn, staff_user):
    service = _make_service(mock_conn)
    data = CategoryUpdateRequest(name="New Name")

    with pytest.raises(HTTPException) as exc:
        await service.update_category(1, data, staff_user)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_update_category_not_found_raises_404(mock_conn, admin_user):
    repo = AsyncMock()
    repo.get_by_id.return_value = None  # doesn't exist

    service = _make_service(mock_conn, repo)
    data = CategoryUpdateRequest(name="X")

    with pytest.raises(HTTPException) as exc:
        await service.update_category(99, data, admin_user)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_category_circular_reference_raises_400(
    mock_conn, admin_user, sample_category
):
    repo = AsyncMock()
    repo.get_by_id.return_value = sample_category  # the category itself exists

    service = _make_service(mock_conn, repo)
    # Set parent_id to same as category_id (circular)
    data = CategoryUpdateRequest(parent_id=1)

    with pytest.raises(HTTPException) as exc:
        await service.update_category(1, data, admin_user)

    assert exc.value.status_code == 400
    assert "own parent" in exc.value.detail


@pytest.mark.asyncio
async def test_update_category_new_parent_not_found_raises_404(
    mock_conn, admin_user, sample_category
):
    repo = AsyncMock()
    # First call: category itself found; second call: parent not found
    repo.get_by_id.side_effect = [sample_category, None]

    service = _make_service(mock_conn, repo)
    data = CategoryUpdateRequest(parent_id=99)

    with pytest.raises(HTTPException) as exc:
        await service.update_category(1, data, admin_user)

    assert exc.value.status_code == 404


# ─── delete_category ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_category_admin_success(mock_conn, admin_user):
    repo = AsyncMock()
    repo.list_children.return_value = []  # no children
    repo.delete.return_value = True

    service = _make_service(mock_conn, repo)
    await service.delete_category(1, admin_user)

    repo.delete.assert_called_once_with(
        category_id=1, tenant_id=admin_user.tenant_id
    )


@pytest.mark.asyncio
async def test_delete_category_staff_raises_403(mock_conn, staff_user):
    service = _make_service(mock_conn)

    with pytest.raises(HTTPException) as exc:
        await service.delete_category(1, staff_user)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_delete_category_not_found_raises_404(mock_conn, admin_user):
    repo = AsyncMock()
    repo.list_children.return_value = []
    repo.delete.return_value = False  # nothing was deleted

    service = _make_service(mock_conn, repo)

    with pytest.raises(HTTPException) as exc:
        await service.delete_category(999, admin_user)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_category_with_children_raises_400(
    mock_conn, admin_user, sample_child_category
):
    repo = AsyncMock()
    repo.list_children.return_value = [sample_child_category]  # has children

    service = _make_service(mock_conn, repo)

    with pytest.raises(HTTPException) as exc:
        await service.delete_category(1, admin_user)

    assert exc.value.status_code == 400
    assert "child" in exc.value.detail


# ─── get_product_distribution_by_category ────────────────────────────────────


@pytest.mark.asyncio
async def test_get_product_distribution_success(mock_conn, admin_user):
    repo = AsyncMock()
    repo.get_product_count_by_category.return_value = [
        {"category_id": 1, "category_name": "Electronics", "product_count": 3},
        {"category_id": 2, "category_name": "Clothing", "product_count": 1},
    ]

    service = _make_service(mock_conn, repo)
    result = await service.get_product_distribution_by_category(admin_user)

    assert result.total_products == 4
    assert len(result.distribution) == 2
    assert result.distribution[0].percentage == 75.0
    assert result.distribution[1].percentage == 25.0


@pytest.mark.asyncio
async def test_get_product_distribution_empty(mock_conn, admin_user):
    repo = AsyncMock()
    repo.get_product_count_by_category.return_value = []

    service = _make_service(mock_conn, repo)
    result = await service.get_product_distribution_by_category(admin_user)

    assert result.total_products == 0
    assert result.distribution == []
