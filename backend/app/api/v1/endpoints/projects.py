"""
CivilInc Project Endpoints
Infrastructure project management API.
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, or_

from app.db.base import get_db
from app.core.dependencies import get_current_user, require_permission, PaginationParams
from app.core.permissions import Permission, Role
from app.models.user import User
from app.models.project import Project
from app.services.project_service import ProjectService
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    department_id: Optional[UUID] = Query(None),
    ward_number: Optional[str] = Query(None),
    at_risk: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conditions = [Project.is_deleted == False]

    # Citizens only see public projects
    if current_user.role == Role.CITIZEN:
        conditions.append(Project.is_public == True)

    if status:
        conditions.append(Project.status == status)
    if category:
        conditions.append(Project.category == category)
    if department_id:
        conditions.append(Project.department_id == department_id)
    if ward_number:
        conditions.append(Project.ward_number == ward_number)
    if at_risk:
        conditions.append(Project.delay_probability >= 0.7)
    if search:
        conditions.append(or_(
            Project.title.ilike(f"%{search}%"),
            Project.project_number.ilike(f"%{search}%"),
        ))

    total = (await db.execute(select(func.count()).select_from(Project).where(and_(*conditions)))).scalar()
    items = (await db.execute(
        select(Project).where(and_(*conditions))
        .order_by(desc(Project.created_at))
        .limit(pagination.limit).offset(pagination.offset)
    )).scalars().all()

    return PaginatedResponse.build(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    current_user: User = Depends(require_permission(Permission.PROJECT_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    svc = ProjectService(db)
    return await svc.create_project(data, current_user)


@router.get("/at-risk", response_model=list[ProjectResponse])
async def get_at_risk_projects(
    threshold: float = Query(0.7, ge=0.0, le=1.0),
    current_user: User = Depends(require_permission(Permission.PROJECT_VIEW_ALL)),
    db: AsyncSession = Depends(get_db),
):
    svc = ProjectService(db)
    return await svc.get_at_risk_projects(threshold)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if current_user.role == Role.CITIZEN and not project.is_public:
        raise HTTPException(status_code=403, detail="Forbidden")
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        svc = ProjectService(db)
        return await svc.update_project(project_id, data, current_user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: UUID,
    current_user: User = Depends(require_permission(Permission.PROJECT_DELETE)),
    db: AsyncSession = Depends(get_db),
):
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await repo.soft_delete(project)
