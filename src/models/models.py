"""
Domain models — single source of truth for all dataclasses and enums.

Every repository and service layer imports models from here (SRP).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


# ─── Enums ───────────────────────────────────────────────────────────────────

class UserRole(str, Enum):
    ADMIN = "Admin"
    STAFF = "Staff"


class TransactionType(str, Enum):
    IN = "In"
    OUT = "Out"
    TRANSFER = "Transfer"


class OperationType(str, Enum):
    PURCHASE = "Purchase"
    SALE = "Sale"
    TRANSFER = "Transfer"
    ADJUSTMENT = "Adjustment"
    RETURN = "Return"


class TransactionStatus(str, Enum):
    DRAFT = "Draft"
    PENDING = "Pending"
    COMPLETED = "Completed"
    FAILED = "Failed"


class OperationStatus(str, Enum):
    DRAFT = "Draft"
    PENDING = "Pending"
    IN_TRANSIT = "In_Transit"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    FAILED = "Failed"

# ─── Tenant ──────────────────────────────────────────────────────────────────

@dataclass
class Tenant:
    id: int
    name: str
    created_at: datetime


# ─── User ────────────────────────────────────────────────────────────────────

@dataclass
class User:
    id: int
    tenant_id: int
    name: str
    email: str
    password_hash: str
    role: UserRole


# ─── Category ────────────────────────────────────────────────────────────────

@dataclass
class Category:
    id: int
    tenant_id: int
    name: str
    parent_id: int | None


# ─── Warehouse ───────────────────────────────────────────────────────────────

@dataclass
class Warehouse:
    id: int
    tenant_id: int
    name: str
    location: str | None


# ─── Product ─────────────────────────────────────────────────────────────────

@dataclass
class Product:
    id: int
    tenant_id: int
    category_id: int | None
    sku: str
    name: str
    description: str | None
    reorder_point: int


# ─── Stock ───────────────────────────────────────────────────────────────────

@dataclass
class Stock:
    product_id: int
    warehouse_id: int
    quantity: int


# ─── Inventory Transaction ──────────────────────────────────────────────────


@dataclass
class InventoryOperation:
    id: int
    tenant_id: int
    user_id: int | None
    operation_type: OperationType
    status: OperationStatus
    source_warehouse_id: int | None
    destination_warehouse_id: int | None
    reference_code: str | None
    note: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class InventoryTransaction:
    id: int
    tenant_id: int
    operation_id: int | None
    product_id: int
    user_id: int | None
    warehouse_id: int | None
    type: TransactionType
    quantity: int
    note: str | None
    timestamp: datetime
    movement_status: TransactionStatus


# ─── Report DTOs ─────────────────────────────────────────────────────────────

@dataclass
class LowStockRow:
    product_id: int
    sku: str
    name: str
    reorder_point: int
    total_stock: int


@dataclass
class MovementHistoryRow:
    id: int
    type: TransactionType
    quantity: int
    warehouse_id: int | None
    user_id: int | None
    note: str | None
    timestamp: datetime