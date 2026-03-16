"""
Database connection pool management.
"""

from __future__ import annotations

import os
import asyncpg
from fastapi import Request


async def create_pool(dsn: str, min_size: int = 2, max_size: int = 10, ssl: str = None) -> asyncpg.Pool:
    """
    Create and initialize the database connection pool.
    
    Args:
        dsn: Database connection string
        min_size: Minimum number of connections in the pool
        max_size: Maximum number of connections in the pool
        ssl: SSL mode for the connection ('require', 'prefer', 'disable', etc.)
        
    Returns:
        Database connection pool
    """
    pool = await asyncpg.create_pool(
        dsn=dsn,
        min_size=min_size,
        max_size=max_size,
        ssl=ssl
    )
    print("✓ Database connection pool created")
    return pool


async def close_pool(pool: asyncpg.Pool) -> None:
    """Close the database connection pool."""
    await pool.close()
    print("✓ Database connection pool closed")


def get_pool(request: Request) -> asyncpg.Pool:
    """
    Get the database connection pool from application state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Database connection pool
        
    Raises:
        RuntimeError: If pool is not initialized in app state
    """
    if not hasattr(request.app.state, "db_pool"):
        raise RuntimeError("Database pool not initialized in app.state")
    return request.app.state.db_pool