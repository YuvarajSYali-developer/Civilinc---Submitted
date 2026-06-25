"""
CivilInc User Management Endpoints
CRUD for officers, coordinators, and citizens.
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.core.dependencies import get_current_user, require_permission, PaginationParams
from app.core.permissions import Permission, Role
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate, UserAdminUpdate, UserResponse
from app.schemas.common import PaginatedResponse, APIResponse
from app.core.security import security

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    role: Optional[str] = Query(None),
    department_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_permission(Permission.USER_VIEW_ALL)),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select, func, and_, or_, desc
    from app.models.user import User as UserModel

    conditions = [UserModel.is_deleted == False]
    if role:
        conditions.append(UserModel.role == role)
    if department_id:
        conditions.append(UserModel.department_id == department_id)
    if is_active is not None:
        conditions.append(UserModel.is_active == is_active)
    if search:
        conditions.append(
            or_(
                UserModel.full_name.ilike(f"%{search}%"),
                UserModel.email.ilike(f"%{search}%"),
                UserModel.employee_id.ilike(f"%{search}%"),
            )
        )

    from sqlalchemy.ext.asyncio import AsyncSession
    count_q = select(func.count()).select_from(UserModel).where(and_(*conditions))
    total = (await db.execute(count_q)).scalar()

    q = (
        select(UserModel).where(and_(*conditions))
        .order_by(desc(UserModel.created_at))
        .limit(pagination.limit).offset(pagination.offset)
    )
    users = (await db.execute(q)).scalars().all()

    return PaginatedResponse.build(
        items=users, total=total, page=pagination.page, page_size=pagination.page_size
    )


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    data: UserCreate,
    current_user: User = Depends(require_permission(Permission.USER_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    existing = await repo.get_by_email(data.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    obj = data.model_dump()
    obj["hashed_password"] = security.hash_password(obj.pop("password"))
    obj["email"] = obj["email"].lower()
    obj["is_active"] = True
    obj["is_verified"] = True  # Admin-created users are pre-verified

    user = await repo.create(obj)
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Own profile always allowed; others need USER_VIEW_ALL
    from app.core.permissions import has_permission
    if user_id != current_user.id and not has_permission(current_user.role, Permission.USER_VIEW_ALL):
        raise HTTPException(status_code=403, detail="Forbidden")

    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    data: UserAdminUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.core.permissions import has_permission
    is_own = user_id == current_user.id
    is_admin = has_permission(current_user.role, Permission.USER_UPDATE)

    if not is_own and not is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")

    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Citizens can't promote themselves
    updates = data.model_dump(exclude_none=True)
    if not is_admin:
        updates.pop("role", None)
        updates.pop("is_active", None)
        updates.pop("department_id", None)

    return await repo.update(user, updates)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_permission(Permission.USER_DELETE)),
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    await repo.soft_delete(user)
