"""
CivilInc Auth Endpoints
Login, register, token refresh, password management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import (
    LoginRequest, TokenResponse, RegisterRequest, RefreshRequest,
    ChangePasswordRequest, UserSummary,
)
from app.core.dependencies import get_current_user
from app.models.user import User
from app.core.security import security

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT tokens."""
    try:
        svc = AuthService(db)
        return await svc.login(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/register", response_model=UserSummary, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new citizen account."""
    try:
        svc = AuthService(db)
        user = await svc.register_citizen(request)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token using refresh token."""
    try:
        svc = AuthService(db)
        return await svc.refresh_access_token(request.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/me", response_model=UserSummary)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get currently authenticated user info."""
    return current_user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change password for the authenticated user."""
    if not security.verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    from datetime import datetime, timezone
    from app.repositories.user_repository import UserRepository
    repo = UserRepository(db)
    await repo.update(current_user, {
        "hashed_password": security.hash_password(request.new_password),
        "password_changed_at": datetime.now(timezone.utc).isoformat(),
    })


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user: User = Depends(get_current_user)):
    """Logout endpoint — client should discard tokens. Server-side blacklisting via Redis in prod."""
    pass
