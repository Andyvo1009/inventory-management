"""
Shared pytest fixtures for service and repository unit tests.

All tests are pure unit tests — repositories and asyncpg connections are mocked,
so no real database connection is required. This keeps the suite fast and
suitable for CI/CD.

Fixtures provided:
  Users:      admin_user, staff_user
  Domain:     sample_tenant, sample_category, sample_child_category,
              sample_product, sample_warehouse, sample_warehouse_b
  Operations: sample_inventory_operation, sample_inventory_transaction
  Rows:       sample_transaction_row (dict mimicking asyncpg Record)
  Infra:      mock_conn (AsyncMock asyncpg connection with transaction support)
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from models.models import (
    Category,
    InventoryOperation,
    InventoryTransaction,
    OperationStatus,
    OperationType,
    Product,
    Tenant,
    TransactionStatus,
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
    """
    A dict that mimics an asyncpg Record for a single inventory transaction.
    Includes all fields required by TransactionResponse (operation_id, movement_status).
    """
    return {
        "id": 1,
        "tenant_id": 1,
        "type": TransactionType.IN,
        "product_id": 1,
        "product_name": "Test Product",
        "product_sku": "SKU-001",
        "operation_id": 1,
        "quantity": 10,
        "origin_warehouse_id": None,
        "origin_warehouse_name": None,
        "des_warehouse_id": 1,
        "des_warehouse_name": "Main Warehouse",
        "user_id": 1,
        "user_name": "Admin User",
        "note": None,
        "timestamp": datetime(2024, 6, 1, 12, 0, 0),
        "movement_status": "Completed",
    }


# ─── Operation / Transaction domain objects ───────────────────────────────────


@pytest.fixture
def sample_inventory_operation() -> InventoryOperation:
    """A PENDING PURCHASE operation with one destination warehouse."""
    return InventoryOperation(
        id=1,
        tenant_id=1,
        user_id=1,
        operation_type=OperationType.PURCHASE,
        status=OperationStatus.PENDING,
        source_warehouse_id=None,
        destination_warehouse_id=1,
        reference_code=None,
        note=None,
        created_at=datetime(2026, 3, 1),
        updated_at=datetime(2026, 3, 1),
    )


@pytest.fixture
def sample_inventory_transaction() -> InventoryTransaction:
    """A single PENDING IN transaction belonging to operation 1."""
    return InventoryTransaction(
        id=1,
        tenant_id=1,
        operation_id=1,
        product_id=1,
        user_id=1,
        warehouse_id=1,
        type=TransactionType.IN,
        quantity=10,
        note=None,
        timestamp=datetime(2026, 3, 1),
        movement_status=TransactionStatus.PENDING,
    )


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
