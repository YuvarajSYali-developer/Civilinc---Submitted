"""
CivilInc Department Endpoints
Municipal department management.
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc

from app.db.base import get_db
from app.core.dependencies import get_current_user, require_permission, PaginationParams
from app.core.permissions import Permission
from app.models.user import User
from app.models.department import Department
from app.repositories.base import BaseRepository
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("", response_model=PaginatedResponse[DepartmentResponse])
async def list_departments(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import or_
    conditions = [Department.is_deleted == False]
    if status:
        conditions.append(Department.status == status)
    if search:
        conditions.append(or_(
            Department.name.ilike(f"%{search}%"),
            Department.code.ilike(f"%{search}%"),
        ))

    total = (await db.execute(select(func.count()).select_from(Department).where(and_(*conditions)))).scalar()
    depts = (await db.execute(
        select(Department).where(and_(*conditions))
        .order_by(Department.name).limit(pagination.limit).offset(pagination.offset)
    )).scalars().all()

    return PaginatedResponse.build(items=depts, total=total, page=pagination.page, page_size=pagination.page_size)


@router.post("", response_model=DepartmentResponse, status_code=201)
async def create_department(
    data: DepartmentCreate,
    current_user: User = Depends(require_permission(Permission.DEPT_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    existing = (await db.execute(select(Department).where(Department.code == data.code.upper()))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Department code already exists")

    obj = data.model_dump()
    obj["code"] = obj["code"].upper()
    dept = Department(**obj)
    db.add(dept)
    await db.flush()
    await db.refresh(dept)
    return dept


@router.get("/{dept_id}", response_model=DepartmentResponse)
async def get_department(
    dept_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    dept = (await db.execute(select(Department).where(Department.id == dept_id, Department.is_deleted == False))).scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    return dept


@router.patch("/{dept_id}", response_model=DepartmentResponse)
async def update_department(
    dept_id: UUID,
    data: DepartmentUpdate,
    current_user: User = Depends(require_permission(Permission.DEPT_UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    dept = (await db.execute(select(Department).where(Department.id == dept_id, Department.is_deleted == False))).scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    for k, v in data.model_dump(exclude_none=True).items():
        setattr(dept, k, v)
    await db.flush()
    await db.refresh(dept)
    return dept


@router.get("/{dept_id}/stats")
async def get_department_stats(
    dept_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.repositories.complaint_repository import ComplaintRepository
    repo = ComplaintRepository(db)
    stats = await repo.get_department_stats(dept_id)
    return {"department_id": str(dept_id), "complaint_stats": stats}
