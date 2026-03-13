"""
Core dependencies for repository injection.
"""

from __future__ import annotations

from typing import Annotated, AsyncGenerator, TypeVar, Type

import asyncpg
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db.pool import get_pool
from models.models import User, UserRole
from .connection import get_connection
from services.auth_service import AuthService
from services.dashboard_service import DashboardService
from services.product_service import ProductService
from services.warehouse_service import WarehouseService
from services.transaction_service import TransactionService
from services.user_service import UserService
from services.category_service import CategoryService

security = HTTPBearer()



async def get_auth_service(
    conn: asyncpg.Connection = Depends(get_connection),
) -> AuthService:
    return AuthService(conn)

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    """Dependency to get the current authenticated user from JWT token."""
    token = credentials.credentials
    return await auth_service.get_user_from_token(token)

async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Dependency to get the current authenticated user and verify Admin role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for this operation",
        )
    return current_user

async def get_dashboard_service(
    conn: asyncpg.Connection = Depends(get_connection),
) -> DashboardService:
    return DashboardService(conn)

async def get_product_service(
    conn: asyncpg.Connection = Depends(get_connection),
) -> ProductService:
    return ProductService(conn)

async def get_warehouse_service(
    conn: asyncpg.Connection = Depends(get_connection),
) -> WarehouseService:
    return WarehouseService(conn)

async def get_transaction_service(
    conn: asyncpg.Connection = Depends(get_connection),
) -> TransactionService:
    return TransactionService(conn)

async def get_user_service(
    conn: asyncpg.Connection = Depends(get_connection),
) -> UserService:
    return UserService(conn)

async def get_category_service(
    conn: asyncpg.Connection = Depends(get_connection),
) -> CategoryService:
    return CategoryService(conn)