"""
Repositories package — public API.

Import interfaces for type-hinting in services (DIP),
and concrete classes for wiring / dependency injection.
"""

# ── Interfaces (depend on these in services) ─────────────────────────────────
from repositories.interfaces import (
    ICategoryRepository,
    IProductRepository,
    IReportRepository,
    IStockRepository,
    ITenantRepository,
    ITransactionRepository,
    IUserRepository,
    IWarehouseRepository,
)

# ── Concrete implementations ─────────────────────────────────────────────────
from repositories.category_repository import CategoryRepository
from repositories.product_repository import ProductRepository
from repositories.report_repository import ReportRepository
from repositories.stock_repository import StockRepository
from repositories.tenant_repository import TenantRepository
from repositories.transaction_repository import TransactionRepository
from repositories.user_repository import UserRepository
from repositories.warehouse_repository import WarehouseRepository

__all__ = [
    # Interfaces
    "ICategoryRepository",
    "IProductRepository",
    "IReportRepository",
    "IStockRepository",
    "ITenantRepository",
    "ITransactionRepository",
    "IUserRepository",
    "IWarehouseRepository",
    # Concrete
    "CategoryRepository",
    "ProductRepository",
    "ReportRepository",
    "StockRepository",
    "TenantRepository",
    "TransactionRepository",
    "UserRepository",
    "WarehouseRepository",
]
