"""
Authentication endpoints - login, register, password management.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from models.models import User
from schemas.auth_schema import (
    RegisterRequest,
    LoginRequest,
    ChangePasswordRequest,
    TokenResponse,
    UserResponse,
)
from core.dependencies import get_auth_service, get_current_user
from services.auth_service import AuthService

# ─── Configuration ───────────────────────────────────────────────────────────

security = HTTPBearer()
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ─── Dependencies ────────────────────────────────────────────────────────────






# ─── Endpoints ───────────────────────────────────────────────────────────────


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    """
    Register a new user.
    
    - **tenant_id**: The tenant this user belongs to
    - **name**: User's full name
    - **email**: User's email (must be unique)
    - **password**: Plain text password (will be hashed)
    - **role**: User role (Admin or Staff)

    """
    print("Registering user with data:", data)
    return await auth_service.register_user(data)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """
    Login with email and password to get an access token.
    
    - **email**: User's email
    - **password**: User's password
    """
    return await auth_service.authenticate_user(data)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)]
) -> UserResponse:
    """
    Get current authenticated user's information.
    
    Requires: Bearer token in Authorization header
    """
    return UserResponse.from_user(current_user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """
    Change the current user's password.
    
    - **old_password**: Current password
    - **new_password**: New password
    
    Requires: Bearer token in Authorization header
    """
    await auth_service.change_user_password(current_user, data)



