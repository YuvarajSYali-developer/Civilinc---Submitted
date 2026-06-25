"""
CivilInc FastAPI Dependencies
Authentication, authorization, pagination, rate limiting.
"""
from typing import Optional, Annotated
from uuid import UUID
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.base import get_db
from app.core.security import security
from app.core.permissions import Role, Permission, has_permission
from app.models.user import User
from app.core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate JWT, return the authenticated user."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = security.decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise ValueError("Not an access token")
        user_id: str = payload.get("sub")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(
        select(User).where(User.id == UUID(user_id), User.is_deleted == False)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_permission(permission: Permission):
    """Factory: returns a dependency that enforces a specific permission."""
    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if not has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value} required",
            )
        return current_user
    return _check


def require_role(*roles: Role):
    """Factory: enforces that the user has one of the given roles."""
    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {[r.value for r in roles]}",
            )
        return current_user
    return _check


class PaginationParams:
    def __init__(
        self,
        page: int = 1,
        page_size: int = settings.DEFAULT_PAGE_SIZE,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ):
        if page < 1:
            raise HTTPException(status_code=422, detail="Page must be >= 1")
        if page_size < 1 or page_size > settings.MAX_PAGE_SIZE:
            raise HTTPException(status_code=422, detail=f"page_size must be 1–{settings.MAX_PAGE_SIZE}")
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size
        self.sort_by = sort_by
        self.sort_order = sort_order.lower()

    @property
    def limit(self) -> int:
        return self.page_size
