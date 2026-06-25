"""
CivilInc Complaint Endpoints
Full complaint lifecycle with AI predictions.
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, or_

from app.db.base import get_db
from app.core.dependencies import get_current_user, require_permission, PaginationParams
from app.core.permissions import Permission, Role
from app.models.user import User
from app.models.complaint import Complaint
from app.services.complaint_service import ComplaintService
from app.repositories.complaint_repository import ComplaintRepository
from app.schemas.complaint import ComplaintCreate, ComplaintUpdate, ComplaintFeedback, ComplaintResponse, ComplaintHistoryResponse
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.get("", response_model=PaginatedResponse[ComplaintResponse])
async def list_complaints(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    ward_number: Optional[str] = Query(None),
    department_id: Optional[UUID] = Query(None),
    assigned_officer_id: Optional[UUID] = Query(None),
    sla_breached: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conditions = [Complaint.is_deleted == False]

    # Citizens only see their own complaints
    if current_user.role == Role.CITIZEN:
        conditions.append(Complaint.citizen_id == current_user.id)

    if status:
        conditions.append(Complaint.status == status)
    if priority:
        conditions.append(Complaint.priority == priority)
    if category:
        conditions.append(Complaint.category == category)
    if ward_number:
        conditions.append(Complaint.ward_number == ward_number)
    if department_id:
        conditions.append(Complaint.department_id == department_id)
    if assigned_officer_id:
        conditions.append(Complaint.assigned_officer_id == assigned_officer_id)
    if sla_breached is not None:
        conditions.append(Complaint.sla_breached == sla_breached)
    if search:
        conditions.append(or_(
            Complaint.title.ilike(f"%{search}%"),
            Complaint.complaint_number.ilike(f"%{search}%"),
            Complaint.description.ilike(f"%{search}%"),
        ))

    total = (await db.execute(select(func.count()).select_from(Complaint).where(and_(*conditions)))).scalar()
    items = (await db.execute(
        select(Complaint).where(and_(*conditions))
        .order_by(desc(Complaint.created_at))
        .limit(pagination.limit).offset(pagination.offset)
    )).scalars().all()

    return PaginatedResponse.build(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.post("", response_model=ComplaintResponse, status_code=201)
async def create_complaint(
    data: ComplaintCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ComplaintService(db)
    complaint = await svc.create_complaint(data, current_user)

    # AI processing queued in background
    background_tasks.add_task(_run_ai_triage, complaint.id, complaint.title, complaint.description)
    return complaint


@router.get("/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint(
    complaint_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ComplaintRepository(db)
    complaint = await repo.get_by_id(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Citizens can only view their own
    if current_user.role == Role.CITIZEN and complaint.citizen_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return complaint


@router.patch("/{complaint_id}", response_model=ComplaintResponse)
async def update_complaint(
    complaint_id: UUID,
    data: ComplaintUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        svc = ComplaintService(db)
        return await svc.update_complaint(complaint_id, data, current_user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/{complaint_id}/feedback", response_model=ComplaintResponse)
async def submit_feedback(
    complaint_id: UUID,
    data: ComplaintFeedback,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        svc = ComplaintService(db)
        return await svc.submit_feedback(complaint_id, data, current_user)
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{complaint_id}/history", response_model=list[ComplaintHistoryResponse])
async def get_complaint_history(
    complaint_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.complaint_history import ComplaintHistory
    result = await db.execute(
        select(ComplaintHistory)
        .where(ComplaintHistory.complaint_id == complaint_id)
        .order_by(ComplaintHistory.created_at.asc())
    )
    return result.scalars().all()


@router.post("/{complaint_id}/escalate", status_code=204)
async def escalate_complaint(
    complaint_id: UUID,
    current_user: User = Depends(require_permission(Permission.COMPLAINT_ESCALATE)),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timezone
    repo = ComplaintRepository(db)
    complaint = await repo.get_by_id(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    await repo.update(complaint, {
        "escalation_level": complaint.escalation_level + 1,
        "escalated_at": datetime.now(timezone.utc).isoformat(),
        "status": "escalated",
    })
    await repo.add_history({
        "complaint_id": complaint.id,
        "actor_id": current_user.id,
        "action": "escalated",
        "comment": f"Escalated to level {complaint.escalation_level + 1}",
    })


async def _run_ai_triage(complaint_id: UUID, title: str, description: str):
    """Background task: run AI predictions on new complaint."""
    # Stub — will be wired to real AI service in Phase 3
    pass
