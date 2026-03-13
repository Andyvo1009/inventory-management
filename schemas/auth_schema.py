from __future__ import annotations

# ─── Schemas ─────────────────────────────────────────────────────────────────

from pydantic import BaseModel, EmailStr
from models.models import User, UserRole


class RegisterRequest(BaseModel):
    tenant_name: str
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.ADMIN


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    email: str
    role: UserRole

    @classmethod
    def from_user(cls, user: User) -> UserResponse:
        return cls(
            id=user.id,
            tenant_id=user.tenant_id,
            name=user.name,
            email=user.email,
            role=user.role,
        )
