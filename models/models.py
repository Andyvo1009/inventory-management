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
class InventoryTransaction:
    id: int
    tenant_id: int
    product_id: int
    user_id: int | None
    origin_warehouse_id: int | None
    des_warehouse_id: int | None
    type: TransactionType
    quantity: int
    notes: str | None
    timestamp: datetime


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
    origin_warehouse_id: int | None
    des_warehouse_id: int | None
    user_id: int | None
    notes: str | None
    timestamp: datetime