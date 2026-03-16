"""
Repository interfaces — abstract base classes (DIP / OCP).

Services depend on these ABCs, not on concrete implementations.
Concrete repos must explicitly inherit and implement all abstract methods.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from models.models import (
    Category,
    InventoryTransaction,
    LowStockRow,
    MovementHistoryRow,
    Product,
    Stock,
    Tenant,
    TransactionType,
    User,
    UserRole,
    Warehouse,
)

from schemas.product_schema import ProductResponse
from schemas.transaction_schema import TransactionResponse


# ─── Tenant ──────────────────────────────────────────────────────────────────

class ITenantRepository(ABC):
    @abstractmethod
    async def create(self, name: str) -> Tenant: ...

    @abstractmethod
    async def get_by_id(self, tenant_id: int) -> Tenant | None: ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Tenant | None: ...

    @abstractmethod
    async def list_all(self) -> list[Tenant]: ...

    @abstractmethod
    async def update(self, tenant_id: int, name: str) -> Tenant | None: ...

    @abstractmethod
    async def delete(self, tenant_id: int) -> bool: ...


# ─── User ────────────────────────────────────────────────────────────────────

class IUserRepository(ABC):
    @abstractmethod
    async def create(
        self, tenant_id: int, name: str, email: str, password_hash: str,
        role: UserRole = UserRole.STAFF,
    ) -> User: ...

    @abstractmethod
    async def get_by_id(self, user_id: int, tenant_id: int) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def list_by_tenant(self, tenant_id: int) -> list[User]: ...

    @abstractmethod
    async def list_by_role(self, tenant_id: int, role: UserRole) -> list[User]: ...

    @abstractmethod
    async def update(
        self, user_id: int, tenant_id: int,
        name: str | None = None, email: str | None = None, role: UserRole | None = None,
    ) -> User | None: ...

    @abstractmethod
    async def delete(self, user_id: int, tenant_id: int) -> bool: ...


# ─── Category ────────────────────────────────────────────────────────────────

class ICategoryRepository(ABC):
    @abstractmethod
    async def create(
        self, tenant_id: int, name: str, parent_id: int | None = None,
    ) -> Category: ...

    @abstractmethod
    async def get_by_id(self, category_id: int, tenant_id: int) -> Category | None: ...

    @abstractmethod
    async def list_by_tenant(self, tenant_id: int) -> list[Category]: ...

    @abstractmethod
    async def list_children(self, parent_id: int, tenant_id: int) -> list[Category]: ...

    @abstractmethod
    async def list_roots(self, tenant_id: int) -> list[Category]: ...

    @abstractmethod
    async def update(
        self, category_id: int, tenant_id: int,
        name: str | None = None, parent_id: int | None = None,
    ) -> Category | None: ...

    @abstractmethod
    async def delete(self, category_id: int, tenant_id: int) -> bool: ...


# ─── Warehouse ───────────────────────────────────────────────────────────────

class IWarehouseRepository(ABC):
    @abstractmethod
    async def create(
        self, tenant_id: int, name: str, location: str | None = None,
    ) -> Warehouse: ...

    @abstractmethod
    async def get_by_id(self, warehouse_id: int, tenant_id: int) -> Warehouse | None: ...

    @abstractmethod
    async def list_by_tenant(self, tenant_id: int) -> list[Warehouse]: ...

    @abstractmethod
    async def update(
        self, warehouse_id: int, tenant_id: int,
        name: str | None = None, location: str | None = None,
    ) -> Warehouse | None: ...

    @abstractmethod
    async def delete(self, warehouse_id: int, tenant_id: int) -> bool: ...


# ─── Product ─────────────────────────────────────────────────────────────────

class IProductRepository(ABC):
    @abstractmethod
    async def create(
        self, tenant_id: int, sku: str, name: str,
        description: str | None = None, category_id: int | None = None,
        reorder_point: int = 0,
    ) -> Product: ...

    @abstractmethod
    async def get_by_id(self, product_id: int, tenant_id: int) -> "ProductResponse | None": ...

    @abstractmethod
    async def get_by_sku(self, sku: str, tenant_id: int) -> Product | None: ...

    @abstractmethod
    async def list_by_tenant(
        self, tenant_id: int, category_id: int | None = None,
        search: str | None = None, limit: int = 50, offset: int = 0,
    ) -> "list[ProductResponse]": ...

    @abstractmethod
    async def update(
        self, product_id: int, tenant_id: int,
        name: str | None = None, description: str | None = None,
        category_id: int | None = None, reorder_point: int | None = None,
    ) -> Product | None: ...

    @abstractmethod
    async def delete(self, product_id: int, tenant_id: int) -> bool: ...


# ─── Stock ───────────────────────────────────────────────────────────────────

class IStockRepository(ABC):
    @abstractmethod
    async def get(self, product_id: int, warehouse_id: int) -> Stock | None: ...

    @abstractmethod
    async def list_by_product(self, product_id: int) -> list[Stock]: ...

    @abstractmethod
    async def list_by_warehouse(self, warehouse_id: int) -> list[Stock]: ...

    @abstractmethod
    async def get_total_stock(self, product_id: int) -> int: ...

    @abstractmethod
    async def increment(self, product_id: int, warehouse_id: int, qty: int) -> Stock: ...

    @abstractmethod
    async def decrement(self, product_id: int, warehouse_id: int, qty: int) -> Stock: ...

    @abstractmethod
    async def set_quantity(self, product_id: int, warehouse_id: int, quantity: int) -> Stock: ...


# ─── Transaction (writes + basic reads) ─────────────────────────────────────

class ITransactionRepository(ABC):
    @abstractmethod
    async def record(
        self, tenant_id: int, product_id: int, type: TransactionType, quantity: int,
        origin_warehouse_id: int | None = None, des_warehouse_id: int | None = None,
        user_id: int | None = None, notes: str | None = None,
    ) -> InventoryTransaction: ...

    @abstractmethod
    async def get_by_id(self, tx_id: int, tenant_id: int) -> InventoryTransaction | None: ...

    @abstractmethod
    async def list_by_tenant(
        self, tenant_id: int, type: TransactionType | None = None,
        warehouse_id: int | None = None, product_id: int | None = None,
        limit: int = 100, offset: int = 0,
    ) -> "list[TransactionResponse]": ...

    @abstractmethod
    async def get_by_id_detailed(self, tx_id: int, tenant_id: int) -> "TransactionResponse | None": ...


# ─── Reports (read-only analytics — ISP) ────────────────────────────────────

class IReportRepository(ABC):
    @abstractmethod
    async def movement_history(
        self, product_id: int, tenant_id: int, limit: int = 100, offset: int = 0,
    ) -> list[MovementHistoryRow]: ...

    @abstractmethod
    async def low_stock_report(self, tenant_id: int) -> list[LowStockRow]: ...


# ─── Dashboard (read-only metrics and aggregations) ─────────────────────────

class IDashboardRepository(ABC):
    @abstractmethod
    async def get_total_products(self, tenant_id: int) -> int: ...

    @abstractmethod
    async def get_total_warehouses(self, tenant_id: int) -> int: ...

    @abstractmethod
    async def get_total_transactions(self, tenant_id: int) -> int: ...

    @abstractmethod
    async def get_all_transactions(self, tenant_id: int, limit: int = 100, offset: int = 0) -> list[dict]: ...

    @abstractmethod
    async def get_stock_by_product(self, tenant_id: int) -> list[dict]: ...

    @abstractmethod
    async def get_low_stock_products(self, tenant_id: int) -> list[dict]: ...
