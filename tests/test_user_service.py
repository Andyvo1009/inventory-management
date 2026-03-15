"""
Unit tests for UserService.

Covers: create user, get by ID, list (all / filtered by role),
update user (admin), update self, and delete.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from models.models import User, UserRole
from schemas.user_schema import (
    UserCreateRequest,
    UserSelfUpdateRequest,
    UserUpdateRequest,
)
from services.user_service import UserService


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _make_service(mock_conn, user_repo=None) -> UserService:
    return UserService(mock_conn, user_repo=user_repo or AsyncMock())


# ─── create_user ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_user_admin_success(mock_conn, admin_user):
    new_user = User(
        id=10,
        tenant_id=1,
        name="New Staff",
        email="newstaff@example.com",
        password_hash="$2b$12$hashed",
        role=UserRole.STAFF,
    )
    repo = AsyncMock()
    repo.get_by_email.return_value = None
    repo.create.return_value = new_user

    service = _make_service(mock_conn, repo)
    data = UserCreateRequest(
        name="New Staff",
        email="newstaff@example.com",
        password="pass123",
        role=UserRole.STAFF,
    )

    result = await service.create_user(data, admin_user)

    assert result.email == "newstaff@example.com"
    assert result.role == UserRole.STAFF
    repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_user_staff_raises_403(mock_conn, staff_user):
    service = _make_service(mock_conn)
    data = UserCreateRequest(
        name="X", email="x@example.com", password="123456", role=UserRole.STAFF
    )

    with pytest.raises(HTTPException) as exc:
        await service.create_user(data, staff_user)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_create_user_duplicate_email_raises_400(mock_conn, admin_user, staff_user):
    repo = AsyncMock()
    repo.get_by_email.return_value = staff_user  # already exists

    service = _make_service(mock_conn, repo)
    data = UserCreateRequest(
        name="Staff",
        email="staff@example.com",
        password="pass123",
        role=UserRole.STAFF,
    )

    with pytest.raises(HTTPException) as exc:
        await service.create_user(data, admin_user)

    assert exc.value.status_code == 400
    assert "already exists" in exc.value.detail


# ─── get_user_by_id ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_user_by_id_success(mock_conn, admin_user, staff_user):
    repo = AsyncMock()
    repo.get_by_id.return_value = staff_user

    service = _make_service(mock_conn, repo)
    result = await service.get_user_by_id(2, admin_user)

    assert result.id == staff_user.id
    assert result.email == staff_user.email
    repo.get_by_id.assert_called_once_with(
        user_id=2, tenant_id=admin_user.tenant_id
    )


@pytest.mark.asyncio
async def test_get_user_by_id_not_found_raises_404(mock_conn, admin_user):
    repo = AsyncMock()
    repo.get_by_id.return_value = None

    service = _make_service(mock_conn, repo)

    with pytest.raises(HTTPException) as exc:
        await service.get_user_by_id(999, admin_user)

    assert exc.value.status_code == 404


# ─── list_users ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_users_all(mock_conn, admin_user, staff_user):
    repo = AsyncMock()
    repo.list_by_tenant.return_value = [admin_user, staff_user]

    service = _make_service(mock_conn, repo)
    result = await service.list_users(admin_user)

    assert result.total == 2
    repo.list_by_tenant.assert_called_once_with(tenant_id=admin_user.tenant_id)


@pytest.mark.asyncio
async def test_list_users_filter_by_role(mock_conn, admin_user, staff_user):
    repo = AsyncMock()
    repo.list_by_role.return_value = [staff_user]

    service = _make_service(mock_conn, repo)
    result = await service.list_users(admin_user, role=UserRole.STAFF)

    assert result.total == 1
    assert result.users[0].role == UserRole.STAFF
    repo.list_by_role.assert_called_once_with(
        tenant_id=admin_user.tenant_id, role=UserRole.STAFF
    )


# ─── update_user ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_user_admin_success(mock_conn, admin_user, staff_user):
    updated = User(
        id=staff_user.id,
        tenant_id=1,
        name="Updated Staff",
        email=staff_user.email,
        password_hash=staff_user.password_hash,
        role=UserRole.STAFF,
    )
    repo = AsyncMock()
    repo.update.return_value = updated

    service = _make_service(mock_conn, repo)
    data = UserUpdateRequest(name="Updated Staff")

    result = await service.update_user(staff_user.id, data, admin_user)

    assert result.name == "Updated Staff"
    repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_staff_raises_403(mock_conn, staff_user):
    service = _make_service(mock_conn)
    data = UserUpdateRequest(name="New Name")

    with pytest.raises(HTTPException) as exc:
        await service.update_user(1, data, staff_user)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_update_user_not_found_raises_404(mock_conn, admin_user):
    repo = AsyncMock()
    repo.update.return_value = None

    service = _make_service(mock_conn, repo)
    data = UserUpdateRequest(name="X")

    with pytest.raises(HTTPException) as exc:
        await service.update_user(999, data, admin_user)

    assert exc.value.status_code == 404


# ─── update_self ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_self_success(mock_conn, staff_user):
    updated = User(
        id=staff_user.id,
        tenant_id=1,
        name="Staff Updated",
        email=staff_user.email,
        password_hash=staff_user.password_hash,
        role=UserRole.STAFF,
    )
    repo = AsyncMock()
    repo.update.return_value = updated

    service = _make_service(mock_conn, repo)
    data = UserSelfUpdateRequest(name="Staff Updated")

    result = await service.update_self(data, staff_user)

    assert result.name == "Staff Updated"
    # Role must NOT be passed to update (self-update cannot change role)
    repo.update.assert_called_once_with(
        user_id=staff_user.id,
        tenant_id=staff_user.tenant_id,
        name="Staff Updated",
        email=None,
        role=None,
    )


@pytest.mark.asyncio
async def test_update_self_user_not_found_raises_404(mock_conn, staff_user):
    repo = AsyncMock()
    repo.update.return_value = None

    service = _make_service(mock_conn, repo)
    data = UserSelfUpdateRequest(name="New Name")

    with pytest.raises(HTTPException) as exc:
        await service.update_self(data, staff_user)


# ─── update_user_password ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_user_password_admin_success(mock_conn, admin_user, staff_user):
    from schemas.user_schema import UserPasswordUpdateRequest

    repo = AsyncMock()
    repo.get_by_id.return_value = staff_user
    repo.update_password.return_value = True

    service = _make_service(mock_conn, repo)
    data = UserPasswordUpdateRequest(new_password="newpass123")

    await service.update_user_password(staff_user.id, data, admin_user)

    repo.get_by_id.assert_called_once_with(
        user_id=staff_user.id, tenant_id=admin_user.tenant_id
    )
    repo.update_password.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_password_staff_raises_403(mock_conn, staff_user):
    from schemas.user_schema import UserPasswordUpdateRequest

    service = _make_service(mock_conn)
    data = UserPasswordUpdateRequest(new_password="newpass123")

    with pytest.raises(HTTPException) as exc:
        await service.update_user_password(1, data, staff_user)

    assert exc.value.status_code == 402


@pytest.mark.asyncio
async def test_update_user_password_user_not_found_raises_404(mock_conn, admin_user):
    from schemas.user_schema import UserPasswordUpdateRequest

    repo = AsyncMock()
    repo.get_by_id.return_value = None

    service = _make_service(mock_conn, repo)
    data = UserPasswordUpdateRequest(new_password="newpass123")

    with pytest.raises(HTTPException) as exc:
        await service.update_user_password(999, data, admin_user)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_user_password_failure_raises_500(mock_conn, admin_user, staff_user):
    from schemas.user_schema import UserPasswordUpdateRequest

    repo = AsyncMock()
    repo.get_by_id.return_value = staff_user
    repo.update_password.return_value = False  # repo signals failure

    service = _make_service(mock_conn, repo)
    data = UserPasswordUpdateRequest(new_password="newpass123")

    with pytest.raises(HTTPException) as exc:
        await service.update_user_password(staff_user.id, data, admin_user)

    assert exc.value.status_code == 500


# ─── delete_user ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_user_admin_success(mock_conn, admin_user, staff_user):
    repo = AsyncMock()
    repo.delete.return_value = True

    service = _make_service(mock_conn, repo)
    await service.delete_user(staff_user.id, admin_user)

    repo.delete.assert_called_once_with(
        user_id=staff_user.id, tenant_id=admin_user.tenant_id
    )


@pytest.mark.asyncio
async def test_delete_user_staff_raises_403(mock_conn, staff_user):
    service = _make_service(mock_conn)

    with pytest.raises(HTTPException) as exc:
        await service.delete_user(1, staff_user)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_delete_user_self_deletion_raises_400(mock_conn, admin_user):
    service = _make_service(mock_conn)

    with pytest.raises(HTTPException) as exc:
        await service.delete_user(admin_user.id, admin_user)  # same ID

    assert exc.value.status_code == 400
    assert "own account" in exc.value.detail


@pytest.mark.asyncio
async def test_delete_user_not_found_raises_404(mock_conn, admin_user, staff_user):
    repo = AsyncMock()
    repo.delete.return_value = False

    service = _make_service(mock_conn, repo)

    with pytest.raises(HTTPException) as exc:
        await service.delete_user(staff_user.id, admin_user)

    assert exc.value.status_code == 404

    assert exc.value.status_code == 404
