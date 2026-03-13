"""
Shared pytest fixtures for service unit tests.

All tests are pure unit tests — repositories are mocked so no real database
connection is required. This keeps the suite fast and suitable for CI/CD.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from models.models import (
    Category,
    Product,
    Tenant,
    TransactionType,
    User,
    UserRole,
    Warehouse,
)


# ─── Users ───────────────────────────────────────────────────────────────────


@pytest.fixture
def admin_user() -> User:
    return User(
        id=1,
        tenant_id=1,
        name="Admin User",
        email="admin@example.com",
        password_hash="$2b$12$fakehash",
        role=UserRole.ADMIN,
    )


@pytest.fixture
def staff_user() -> User:
    return User(
        id=2,
        tenant_id=1,
        name="Staff User",
        email="staff@example.com",
        password_hash="$2b$12$fakehash",
        role=UserRole.STAFF,
    )


# ─── Domain objects ──────────────────────────────────────────────────────────


@pytest.fixture
def sample_tenant() -> Tenant:
    return Tenant(id=1, name="Test Tenant", created_at=datetime(2024, 1, 1))


@pytest.fixture
def sample_category() -> Category:
    return Category(id=1, tenant_id=1, name="Electronics", parent_id=None)


@pytest.fixture
def sample_child_category() -> Category:
    return Category(id=2, tenant_id=1, name="Laptops", parent_id=1)


@pytest.fixture
def sample_product() -> Product:
    return Product(
        id=1,
        tenant_id=1,
        category_id=1,
        sku="SKU-001",
        name="Test Product",
        description="A test product",
        reorder_point=10,
    )


@pytest.fixture
def sample_warehouse() -> Warehouse:
    return Warehouse(id=1, tenant_id=1, name="Main Warehouse", location="Building A")


@pytest.fixture
def sample_warehouse_b() -> Warehouse:
    return Warehouse(id=2, tenant_id=1, name="Secondary Warehouse", location="Building B")


# ─── Transaction response row (mimics asyncpg Record as a dict) ──────────────


@pytest.fixture
def sample_transaction_row() -> dict:
    return {
        "id": 1,
        "tenant_id": 1,
        "type": TransactionType.IN,
        "product_id": 1,
        "product_name": "Test Product",
        "product_sku": "SKU-001",
        "quantity": 10,
        "origin_warehouse_id": None,
        "origin_warehouse_name": None,
        "des_warehouse_id": 1,
        "des_warehouse_name": "Main Warehouse",
        "user_id": 1,
        "user_name": "Admin User",
        "notes": None,
        "timestamp": datetime(2024, 6, 1, 12, 0, 0),
    }


# ─── asyncpg connection mock ─────────────────────────────────────────────────


@pytest.fixture
def mock_conn() -> AsyncMock:
    """
    An AsyncMock that models an asyncpg connection.
    conn.transaction() must be usable as an async context manager.
    """
    conn = AsyncMock()

    # Make conn.transaction() return an async context manager
    mock_transaction = AsyncMock()
    mock_transaction.__aenter__ = AsyncMock(return_value=None)
    mock_transaction.__aexit__ = AsyncMock(return_value=False)
    conn.transaction = MagicMock(return_value=mock_transaction)

    return conn
