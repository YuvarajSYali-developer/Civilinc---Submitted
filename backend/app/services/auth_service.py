"""
CivilInc Auth Service
Authentication and token management business logic.
"""
from datetime import datetime, timezone
from typing import Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import security
from app.core.config import settings
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse, RegisterRequest
from app.models.user import User
from app.core.permissions import Role


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def login(self, request: LoginRequest) -> TokenResponse:
        user = await self.user_repo.get_by_email(request.email.lower())
        if not user or not security.verify_password(request.password, user.hashed_password):
            raise ValueError("Invalid email or password")
        if not user.is_active:
            raise ValueError("Account is deactivated. Contact your administrator.")
        if user.is_deleted:
            raise ValueError("Account not found")

        # Reset failed attempts on success
        await self.user_repo.update(user, {
            "failed_login_attempts": 0,
            "last_login_at": datetime.now(timezone.utc).isoformat(),
        })

        access_token = security.create_access_token(
            subject=user.id,
            role=user.role.value,
            department_id=str(user.department_id) if user.department_id else None,
        )
        refresh_token = security.create_refresh_token(subject=user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
            role=user.role,
            full_name=user.full_name,
        )

    async def register_citizen(self, request: RegisterRequest) -> User:
        existing = await self.user_repo.get_by_email(request.email.lower())
        if existing:
            raise ValueError("Email already registered")

        user = await self.user_repo.create({
            "email": request.email.lower(),
            "full_name": request.full_name,
            "phone": request.phone,
            "ward_number": request.ward_number,
            "hashed_password": security.hash_password(request.password),
            "role": Role.CITIZEN,
            "is_active": True,
            "is_verified": False,
        })
        return user

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        try:
            payload = security.decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise ValueError("Invalid token type")
            user_id = payload.get("sub")
        except Exception:
            raise ValueError("Invalid or expired refresh token")

        from uuid import UUID
        user = await self.user_repo.get_by_id(UUID(user_id))
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")

        access_token = security.create_access_token(
            subject=user.id,
            role=user.role.value,
            department_id=str(user.department_id) if user.department_id else None,
        )
        new_refresh = security.create_refresh_token(subject=user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
            role=user.role,
            full_name=user.full_name,
        )
