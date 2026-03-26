"""
Authentication Service - Business logic for authentication operations.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

import asyncpg
from dotenv import load_dotenv
from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from models.models import User, UserRole
from repositories.interfaces import ITenantRepository, IUserRepository
from repositories.interfaces import ITenantRepository
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository
from schemas.auth_schema import (
    RegisterRequest,
    LoginRequest,
    ChangePasswordRequest,
    TokenResponse,
    UserResponse,
)

# ─── Configuration ───────────────────────────────────────────────────────────

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ─── Password Utilities ──────────────────────────────────────────────────────


def hash_password(password: str) -> str:
    """Hash a plain password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


# ─── JWT Token Utilities ─────────────────────────────────────────────────────


def create_access_token(user_id: int, email: str, tenant_id: int, role: str) -> str:
    """Create a JWT access token."""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "tenant_id": tenant_id,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ─── Authentication Service ──────────────────────────────────────────────────


class AuthService:
    """Service class for authentication operations."""

    def __init__(self, conn: asyncpg.Connection, user_repo: IUserRepository = None, tenant_repo: ITenantRepository = None):
        self._user_repo = user_repo or UserRepository(conn)
        self._tenant_repo = tenant_repo or TenantRepository(conn)

    async def register_user(self, data: RegisterRequest) -> UserResponse:
        """
        Register a new user.
        
        Args:
            data: Registration request data
            
        Returns:
            UserResponse with created user information
            
        Raises:
            HTTPException: If email already exists
        """
        # Check if email already exists
        existing_user = await self._user_repo.get_by_email(data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Hash password and create user
        password_hash = hash_password(data.password)

        # Create a new tenant for this user
        tenant = await self._tenant_repo.create(name=data.tenant_name)
        tenant_id = tenant.id
        role = data.role
        # Create user via repository
        user = await self._user_repo.create(
            tenant_id=tenant_id,
            name=data.name,
            email=data.email,
            password_hash=password_hash,
            role=role,
        )

        return UserResponse.from_user(user)

    async def authenticate_user(self, data: LoginRequest) -> TokenResponse:
        """
        Authenticate user and generate access token.
        
        Args:
            data: Login request data
            
        Returns:
            TokenResponse with access token
            
        Raises:
            HTTPException: If credentials are invalid
        """
        # Fetch user via repository
        user = await self._user_repo.get_by_email(data.email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Verify password
        if not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Create access token
        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            tenant_id=user.tenant_id,
            role=user.role.value,
        )

        return TokenResponse(access_token=access_token)

    async def get_user_from_token(self, token: str) -> User:
        """
        Get user from JWT token.
        
        Args:
            token: JWT access token
            
        Returns:
            User object
            
        Raises:
            HTTPException: If token is invalid or user not found
        """
        payload = decode_access_token(token)

        user_id = int(payload.get("sub"))
        email = payload.get("email")
        if not user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        # Fetch user from database
        user = await self._user_repo.get_by_email(email)

        if user is None or user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        return user

    async def change_user_password(
        self, user: User, data: ChangePasswordRequest
    ) -> None:
        """
        Change user's password.
        
        Args:
            user: Current user
            data: Change password request data
            
        Raises:
            HTTPException: If old password is incorrect
        """
        # Verify old password
        if not verify_password(data.old_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password",
            )

        # Hash new password
        new_password_hash = hash_password(data.new_password)

        # Update password via repository
        await self._user_repo.update_password(user.id, user.tenant_id, new_password_hash)

    @staticmethod
    def validate_admin_role(user: User) -> None:
        """
        Validate that user has admin role.
        
        Args:
            user: User to validate
            
        Raises:
            HTTPException: If user is not an admin
        """
        if user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required",
            )
