"""
User management endpoints - CRUD operations for users.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status, Query

from models.models import User, UserRole
from schemas.user_schema import (
    UserCreateRequest,
    UserUpdateRequest,
    UserSelfUpdateRequest,
    UserPasswordUpdateRequest,
    UserResponse,
    UserListResponse,
)
from core.dependencies import get_user_service, get_current_user, get_current_admin_user
from services.user_service import UserService

# ─── Configuration ───────────────────────────────────────────────────────────

router = APIRouter(prefix="/api/users", tags=["Users"])


# ─── Endpoints ───────────────────────────────────────────────────────────────


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreateRequest,
    current_user: Annotated[User, Depends(get_current_admin_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    """
    Create a new user (Admin only).
    
    - **name**: User's full name
    - **email**: User's email (must be unique)
    - **password**: User's password (minimum 6 characters)
    - **role**: User role (Admin or Staff)
    
    Requires: Admin role
    """
    return await user_service.create_user(data, current_user)


@router.get("/", response_model=UserListResponse)
async def list_users(
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    role: Annotated[UserRole | None, Query(description="Filter by role")] = None,
) -> UserListResponse:
    """
    List all users in the current tenant.
    
    - **role**: Optional - Filter by role (Admin or Staff)
    
    Requires: Authentication
    """
    return await user_service.list_users(current_user, role)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """
    Get current user's profile information.
    
    Requires: Authentication
    """
    return UserResponse.from_user(current_user)


@router.put("/me", response_model=UserResponse)
async def update_self(
    data: UserSelfUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    """
    Update own profile information.
    
    Users can only update their own name. Email and role cannot be changed.
    
    - **name**: Updated full name
    
    Requires: Authentication
    """
    return await user_service.update_self(data, current_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    """
    Get a specific user by ID.
    
    - **user_id**: The ID of the user to retrieve
    
    Requires: Authentication
    """
    return await user_service.get_user_by_id(user_id, current_user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdateRequest,
    current_user: Annotated[User, Depends(get_current_admin_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    """
    Update a user's information (Admin only).
    
    - **user_id**: The ID of the user to update
    - **name**: Optional - New full name
    - **role**: Optional - New role (Admin or Staff)
    
    Note: Email cannot be updated. Only provided fields will be updated.
    
    Requires: Admin role
    """
    # print("Updating user with ID:", user_id,flush=True)
    return await user_service.update_user(user_id, data, current_user)


@router.put("/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
async def update_user_password(
    user_id: int,
    data: UserPasswordUpdateRequest,
    current_user: Annotated[User, Depends(get_current_admin_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """
    Update a user's password (Admin only).
    
    - **user_id**: The ID of the user to update
    - **new_password**: New password (minimum 6 characters)
    
    Requires: Admin role
    """
    await user_service.update_user_password(user_id, data, current_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_admin_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """
    Delete a user (Admin only).
    
    - **user_id**: The ID of the user to delete
    
    Note: Users cannot delete their own account.
    
    Requires: Admin role
    """
    await user_service.delete_user(user_id, current_user)
