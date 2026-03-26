"""
User Repository — concrete asyncpg implementation.
"""

from __future__ import annotations

import asyncpg

from models.models import User, UserRole
from repositories.interfaces import IUserRepository


class UserRepository(IUserRepository):
    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def create(
        self,
        tenant_id: int,
        name: str,
        email: str,
        password_hash: str,
        role: UserRole = UserRole.STAFF,
    ) -> User:
        """Create a new user under a tenant."""
        row = await self._conn.fetchrow(
            """
            INSERT INTO users (tenant_id, name, email, password_hash, role)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, tenant_id, name, email, password_hash, role
            """,
            tenant_id,
            name,
            email,
            password_hash,
            role.value,
        )
        return _row_to_user(row)

    async def get_by_id(self, user_id: int, tenant_id: int) -> User | None:
        row = await self._conn.fetchrow(
            """
            SELECT id, tenant_id, name, email, password_hash, role
            FROM users
            WHERE id = $1 AND tenant_id = $2
            """,
            user_id,
            tenant_id,
        )
        return _row_to_user(row) if row else None

    async def get_by_email(self, email: str) -> User | None:
        row = await self._conn.fetchrow(
            "SELECT id, tenant_id, name, email, password_hash, role FROM users WHERE email = $1",
            email,
        )
        return _row_to_user(row) if row else None

    async def list_by_tenant(self, tenant_id: int) -> list[User]:
        rows = await self._conn.fetch(
            """
            SELECT id, tenant_id, name, email, password_hash, role
            FROM users
            WHERE tenant_id = $1
            ORDER BY name
            """,
            tenant_id,
        )
        return [_row_to_user(r) for r in rows]

    async def list_by_role(self, tenant_id: int, role: UserRole) -> list[User]:
        rows = await self._conn.fetch(
            """
            SELECT id, tenant_id, name, email, password_hash, role
            FROM users
            WHERE tenant_id = $1 AND role = $2
            ORDER BY name
            """,
            tenant_id,
            role.value,
        )
        return [_row_to_user(r) for r in rows]

    async def update(
        self,
        user_id: int,
        tenant_id: int,
        name: str | None = None,
        email: str | None = None,
        role: UserRole | None = None,
    ) -> User | None:
        """Partial update — only provided fields are changed."""
        row = await self._conn.fetchrow(
            """
            UPDATE users
            SET
                name  = COALESCE($3, name),
                email = COALESCE($4, email),
                role  = COALESCE($5, role)
            WHERE id = $1 AND tenant_id = $2
            RETURNING id, tenant_id, name, email, password_hash, role
            """,
            user_id,
            tenant_id,
            name,
            email,
            role.value if role else None,
        )
        return _row_to_user(row) if row else None

    async def delete(self, user_id: int, tenant_id: int) -> bool:
        result = await self._conn.execute(
            "DELETE FROM users WHERE id = $1 AND tenant_id = $2",
            user_id,
            tenant_id,
        )
        return result == "DELETE 1"

    async def update_password(self, user_id: int, tenant_id: int, password_hash: str) -> bool:
        """Update user's password hash."""
        result = await self._conn.execute(
            "UPDATE users SET password_hash = $1 WHERE id = $2 AND tenant_id = $3",
            password_hash,
            user_id,
            tenant_id,
        )
        return result == "UPDATE 1"


def _row_to_user(row: asyncpg.Record) -> User:
    return User(
        id=row["id"],
        tenant_id=row["tenant_id"],
        name=row["name"],
        email=row["email"],
        password_hash=row["password_hash"],
        role=UserRole(row["role"]),
    )
