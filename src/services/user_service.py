"""
User Service - Business logic for user management operations.
"""

from __future__ import annotations
import asyncpg
from fastapi import HTTPException, status

from models.models import User, UserRole
from repositories.interfaces import IUserRepository
from repositories.user_repository import UserRepository
from services.auth_service import hash_password
from schemas.user_schema import (
    UserCreateRequest,
    UserUpdateRequest,
    UserSelfUpdateRequest,
    UserPasswordUpdateRequest,
    UserResponse,
    UserListResponse,
)


class UserService:
    """Service class for user management operations."""

    def __init__(self, conn: asyncpg.Connection, user_repo: IUserRepository = None):
        self._user_repo = user_repo or UserRepository(conn)

    @staticmethod
    def validate_admin_role(user: User):
        """Ensure the user has Admin role, otherwise raise exception."""
        if user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required for this operation",
            )

    async def create_user(
        self, data: UserCreateRequest, current_user: User
    ) -> UserResponse:
        """
        Create a new user (Admin only).
        
        Args:
            data: User creation request data
            current_user: The authenticated user
            
        Returns:
            UserResponse with created user information
            
        Raises:
            HTTPException: If email already exists or user lacks permissions
        """
        # Only admins can create users
        self.validate_admin_role(current_user)

        # Check if email already exists
        existing_user = await self._user_repo.get_by_email(data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email '{data.email}' already exists",
            )

        # Hash password and create user
        password_hash = hash_password(data.password)

        user = await self._user_repo.create(
            tenant_id=current_user.tenant_id,
            name=data.name,
            email=data.email,
            password_hash=password_hash,
            role=data.role,
        )

        return UserResponse.from_user(user)

    async def get_user_by_id(
        self, user_id: int, current_user: User
    ) -> UserResponse:
        """
        Get a user by ID.
        
        Args:
            user_id: User ID
            current_user: The authenticated user
            
        Returns:
            UserResponse with user information
            
        Raises:
            HTTPException: If user not found
        """
        user = await self._user_repo.get_by_id(
            user_id=user_id, tenant_id=current_user.tenant_id
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )

        return UserResponse.from_user(user)

    async def list_users(
        self, current_user: User, role: UserRole | None = None
    ) -> UserListResponse:
        """
        List all users in the tenant.
        
        Args:
            current_user: The authenticated user
            role: Optional role filter
            
        Returns:
            UserListResponse with list of users
        """
        
        # logger.info(f"Listing users for tenant_id={current_user.tenant_id} with role filter={role}")
        if role:
            users = await self._user_repo.list_by_role(
                tenant_id=current_user.tenant_id, role=role
            )
        else:
            users = await self._user_repo.list_by_tenant(
                tenant_id=current_user.tenant_id
            )

        return UserListResponse(
            users=[UserResponse.from_user(u) for u in users],
            total=len(users),
        )

    async def update_user(
        self, user_id: int, data: UserUpdateRequest, current_user: User
    ) -> UserResponse:
        """
        Update a user's information (Admin only).
        
        Args:
            user_id: User ID to update
            data: User update request data
            current_user: The authenticated user
            
        Returns:
            UserResponse with updated user information
            
        Raises:
            HTTPException: If user not found or lacks permissions
        """
        # Only admins can update other users
        self.validate_admin_role(current_user)
        # Update the user
        user = await self._user_repo.update(
            user_id=user_id,
            tenant_id=current_user.tenant_id,
            name=data.name,
            email=None,  # Email cannot be updated
            role=data.role,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )

        return UserResponse.from_user(user)

    async def update_self(
        self, data: UserSelfUpdateRequest, current_user: User
    ) -> UserResponse:
        """
        Update own user information.
        
        Args:
            data: Self update request data
            current_user: The authenticated user
            
        Returns:
            UserResponse with updated user information
        """
        # Users can only update their own name
        user = await self._user_repo.update(
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            name=data.name,
            email=None,  # Email cannot be updated
            role=None,   # Role cannot be self-updated
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return UserResponse.from_user(user)

    async def update_user_password(
        self, user_id: int, data: UserPasswordUpdateRequest, current_user: User
    ) -> None:
        """
        Update a user's password (Admin only).
        
        Args:
            user_id: User ID to update
            data: Password update request data
            current_user: The authenticated user
            
        Raises:
            HTTPException: If user not found or lacks permissions
        """
        # Only admins can update other users' passwords
        self.validate_admin_role(current_user)

        # Verify user exists and belongs to tenant
        user = await self._user_repo.get_by_id(
            user_id=user_id, tenant_id=current_user.tenant_id
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )

        # Hash and update password
        password_hash = hash_password(data.new_password)
        success = await self._user_repo.update_password(user_id, password_hash)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password",
            )

    async def delete_user(
        self, user_id: int, current_user: User
    ) -> None:
        """
        Delete a user (Admin only).
        
        Args:
            user_id: User ID to delete
            current_user: The authenticated user
            
        Raises:
            HTTPException: If user not found or trying to delete self
        """
        # Only admins can delete users
        self.validate_admin_role(current_user)

        # Prevent self-deletion
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account",
            )

        success = await self._user_repo.delete(
            user_id=user_id, tenant_id=current_user.tenant_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )
