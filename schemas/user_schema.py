"""
User Schemas — Request and Response models for user management operations.
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from models.models import User, UserRole


class UserCreateRequest(BaseModel):
    """Request schema for creating a new user (Admin only)."""
    name: str = Field(..., min_length=1, max_length=255, description="User's full name")
    email: EmailStr = Field(..., description="User's email (must be unique)")
    password: str = Field(..., min_length=6, description="User's password")
    role: UserRole = Field(UserRole.STAFF, description="User role (Admin or Staff)")


class UserUpdateRequest(BaseModel):
    """Request schema for updating user info (Admin can update others)."""
    name: str | None = Field(None, min_length=1, max_length=255, description="User's full name")
    role: UserRole | None = Field(None, description="User role (Admin or Staff)")


class UserSelfUpdateRequest(BaseModel):
    """Request schema for updating own info (any authenticated user)."""
    name: str = Field(..., min_length=1, max_length=255, description="User's full name")


class UserPasswordUpdateRequest(BaseModel):
    """Request schema for updating user password (Admin only)."""
    new_password: str = Field(..., min_length=6, description="New password")


class UserResponse(BaseModel):
    """Response schema for user data."""
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


class UserListResponse(BaseModel):
    """Response schema for list of users."""
    users: list[UserResponse]
    total: int
