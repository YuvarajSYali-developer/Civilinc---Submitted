"""
CivilInc Notification Endpoints
User notification management.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, update
from datetime import datetime, timezone

from app.db.base import get_db
from app.core.dependencies import get_current_user, PaginationParams
from app.models.user import User
from app.models.notification import Notification
from app.schemas.common import PaginatedResponse
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class NotificationResponse(BaseModel):
    id: UUID
    title: str
    message: str
    notification_type: str
    is_read: bool
    read_at: Optional[str] = None
    action_url: Optional[str] = None
    icon: Optional[str] = None
    priority: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


@router.get("", response_model=PaginatedResponse[NotificationResponse])
async def list_notifications(
    is_read: Optional[bool] = Query(None),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conditions = [Notification.user_id == current_user.id, Notification.is_deleted == False]
    if is_read is not None:
        conditions.append(Notification.is_read == is_read)

    total = (await db.execute(select(func.count()).select_from(Notification).where(and_(*conditions)))).scalar()
    items = (await db.execute(
        select(Notification).where(and_(*conditions))
        .order_by(desc(Notification.created_at))
        .limit(pagination.limit).offset(pagination.offset)
    )).scalars().all()

    return PaginatedResponse.build(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get("/unread-count")
async def unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = (await db.execute(
        select(func.count()).select_from(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False, Notification.is_deleted == False)
    )).scalar()
    return {"unread_count": count}


@router.patch("/{notification_id}/read", status_code=204)
async def mark_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    notif = (await db.execute(
        select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id)
    )).scalar_one_or_none()
    if notif:
        notif.is_read = True
        notif.read_at = datetime.now(timezone.utc).isoformat()
        await db.flush()


@router.post("/mark-all-read", status_code=204)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
        .values(is_read=True, read_at=datetime.now(timezone.utc).isoformat())
    )
