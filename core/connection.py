from typing import AsyncGenerator
from fastapi import Request
import asyncpg

async def get_connection(request: Request) -> AsyncGenerator[asyncpg.Connection, None]:
    pool = request.app.state.db_pool
    async with pool.acquire() as conn:
        async with conn.transaction():
            yield conn