"""
Unit tests for AuthService.

Covers: password hashing, JWT token creation/decoding, register,
authenticate, and get_user_from_token.
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests")
os.environ.setdefault("ALGORITHM", "HS256")

from models.models import User, UserRole
from schemas.auth_schema import LoginRequest, RegisterRequest
from services.auth_service import (
    AuthService,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


# ─── Password utilities ──────────────────────────────────────────────────────


def test_hash_password_returns_bcrypt_hash():
    hashed = hash_password("secret123")
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")


def test_verify_password_correct():
    plain = "mypassword"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("correct")
    assert verify_password("wrong", hashed) is False


# ─── JWT utilities ───────────────────────────────────────────────────────────


def test_create_and_decode_access_token():
    token = create_access_token(
        user_id=42, email="test@example.com", tenant_id=7, role="Admin"
    )
    payload = decode_access_token(token)

    assert payload["sub"] == "42"
    assert payload["email"] == "test@example.com"
    assert payload["tenant_id"] == 7
    assert payload["role"] == "Admin"


def test_decode_access_token_invalid_raises_401():
    with pytest.raises(HTTPException) as exc:
        decode_access_token("not.a.valid.token")
    assert exc.value.status_code == 401


# ─── AuthService.register_user ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_user_success(mock_conn, sample_tenant, admin_user):
    user_repo = AsyncMock()
    tenant_repo = AsyncMock()

    user_repo.get_by_email.return_value = None
    tenant_repo.create.return_value = sample_tenant
    user_repo.create.return_value = admin_user

    service = AuthService(mock_conn, user_repo=user_repo, tenant_repo=tenant_repo)
    data = RegisterRequest(
        tenant_name="Acme Corp",
        name="Admin User",
        email="admin@example.com",
        password="secure123",
        role=UserRole.ADMIN,
    )

    result = await service.register_user(data)

    assert result.email == "admin@example.com"
    assert result.role == UserRole.ADMIN
    user_repo.create.assert_called_once()
    tenant_repo.create.assert_called_once_with(name="Acme Corp")


@pytest.mark.asyncio
async def test_register_user_duplicate_email_raises_400(mock_conn, admin_user):
    user_repo = AsyncMock()
    tenant_repo = AsyncMock()

    user_repo.get_by_email.return_value = admin_user  # already exists

    service = AuthService(mock_conn, user_repo=user_repo, tenant_repo=tenant_repo)
    data = RegisterRequest(
        tenant_name="Acme",
        name="Admin",
        email="admin@example.com",
        password="pass",
        role=UserRole.ADMIN,
    )

    with pytest.raises(HTTPException) as exc:
        await service.register_user(data)

    assert exc.value.status_code == 400
    assert "already registered" in exc.value.detail


# ─── AuthService.authenticate_user ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_authenticate_user_success(mock_conn):
    plain_password = "correct_password"
    hashed = hash_password(plain_password)

    stored_user = User(
        id=1,
        tenant_id=1,
        name="Admin",
        email="admin@example.com",
        password_hash=hashed,
        role=UserRole.ADMIN,
    )

    user_repo = AsyncMock()
    user_repo.get_by_email.return_value = stored_user

    service = AuthService(mock_conn, user_repo=user_repo)
    data = LoginRequest(email="admin@example.com", password=plain_password)

    result = await service.authenticate_user(data)

    assert result.access_token
    assert result.token_type == "bearer"


@pytest.mark.asyncio
async def test_authenticate_user_not_found_raises_401(mock_conn):
    user_repo = AsyncMock()
    user_repo.get_by_email.return_value = None

    service = AuthService(mock_conn, user_repo=user_repo)
    data = LoginRequest(email="ghost@example.com", password="pass")

    with pytest.raises(HTTPException) as exc:
        await service.authenticate_user(data)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password_raises_401(mock_conn):
    hashed = hash_password("real_password")
    stored_user = User(
        id=1,
        tenant_id=1,
        name="A",
        email="a@example.com",
        password_hash=hashed,
        role=UserRole.ADMIN,
    )

    user_repo = AsyncMock()
    user_repo.get_by_email.return_value = stored_user

    service = AuthService(mock_conn, user_repo=user_repo)
    data = LoginRequest(email="a@example.com", password="wrong_password")

    with pytest.raises(HTTPException) as exc:
        await service.authenticate_user(data)

    assert exc.value.status_code == 401


# ─── AuthService.get_user_from_token ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_user_from_token_success(mock_conn, admin_user):
    token = create_access_token(
        user_id=admin_user.id,
        email=admin_user.email,
        tenant_id=admin_user.tenant_id,
        role=admin_user.role.value,
    )

    user_repo = AsyncMock()
    user_repo.get_by_email.return_value = admin_user

    service = AuthService(mock_conn, user_repo=user_repo)
    result = await service.get_user_from_token(token)

    assert result.id == admin_user.id
    assert result.email == admin_user.email


@pytest.mark.asyncio
async def test_get_user_from_token_invalid_token_raises_401(mock_conn):
    service = AuthService(mock_conn, user_repo=AsyncMock())

    with pytest.raises(HTTPException) as exc:
        await service.get_user_from_token("invalid.token.here")

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_user_from_token_user_not_found_raises_401(mock_conn, admin_user):
    token = create_access_token(
        user_id=admin_user.id,
        email=admin_user.email,
        tenant_id=admin_user.tenant_id,
        role=admin_user.role.value,
    )

    user_repo = AsyncMock()
    user_repo.get_by_email.return_value = None  # user deleted from DB

    service = AuthService(mock_conn, user_repo=user_repo)

    with pytest.raises(HTTPException) as exc:
        await service.get_user_from_token(token)


# ─── AuthService.change_user_password ────────────────────────────────────────


@pytest.mark.asyncio
async def test_change_user_password_success(mock_conn, admin_user):
    from schemas.auth_schema import ChangePasswordRequest

    plain_old = "old_password"
    user_with_hash = User(
        id=admin_user.id,
        tenant_id=admin_user.tenant_id,
        name=admin_user.name,
        email=admin_user.email,
        password_hash=hash_password(plain_old),
        role=admin_user.role,
    )

    user_repo = AsyncMock()
    user_repo.update_password.return_value = True

    service = AuthService(mock_conn, user_repo=user_repo)
    data = ChangePasswordRequest(old_password=plain_old, new_password="new_secure_pass")

    # Should not raise
    await service.change_user_password(user_with_hash, data)

    user_repo.update_password.assert_called_once()
    # First arg is user.id
    assert user_repo.update_password.call_args[0][0] == admin_user.id


@pytest.mark.asyncio
async def test_change_user_password_wrong_old_password_raises_400(mock_conn, admin_user):
    from schemas.auth_schema import ChangePasswordRequest

    user_with_hash = User(
        id=admin_user.id,
        tenant_id=admin_user.tenant_id,
        name=admin_user.name,
        email=admin_user.email,
        password_hash=hash_password("correct_password"),
        role=admin_user.role,
    )

    service = AuthService(mock_conn, user_repo=AsyncMock())
    data = ChangePasswordRequest(old_password="wrong_password", new_password="new_pass")

    with pytest.raises(HTTPException) as exc:
        await service.change_user_password(user_with_hash, data)

    assert exc.value.status_code == 400
    assert "Incorrect" in exc.value.detail

    
