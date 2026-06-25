"""
CivilInc Forum Endpoints
Interdepartmental discussion threads and comments.
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, or_
from datetime import datetime, timezone

from app.db.base import get_db
from app.core.dependencies import get_current_user, require_permission, PaginationParams
from app.core.permissions import Permission
from app.models.user import User
from app.models.forum import ForumThread, ForumComment
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/forum", tags=["Forum"])


class ThreadCreate(BaseModel):
    title: str
    body: str
    category: str = "general"
    department_id: Optional[UUID] = None
    tags: Optional[list] = None
    is_announcement: bool = False


class ThreadResponse(BaseModel):
    id: UUID
    title: str
    body: str
    category: str
    author_id: UUID
    department_id: Optional[UUID] = None
    is_pinned: bool
    is_locked: bool
    is_announcement: bool
    view_count: int
    comment_count: int
    upvotes: int
    tags: Optional[list] = None
    created_at: datetime
    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    body: str
    parent_comment_id: Optional[UUID] = None


class CommentResponse(BaseModel):
    id: UUID
    thread_id: UUID
    author_id: UUID
    body: str
    upvotes: int
    is_solution: bool
    parent_comment_id: Optional[UUID] = None
    created_at: datetime
    class Config:
        from_attributes = True


@router.get("/threads", response_model=PaginatedResponse[ThreadResponse])
async def list_threads(
    category: Optional[str] = Query(None),
    department_id: Optional[UUID] = Query(None),
    pinned_only: bool = Query(False),
    search: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_permission(Permission.FORUM_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    conditions = [ForumThread.is_deleted == False]
    if category:
        conditions.append(ForumThread.category == category)
    if department_id:
        conditions.append(ForumThread.department_id == department_id)
    if pinned_only:
        conditions.append(ForumThread.is_pinned == True)
    if search:
        conditions.append(or_(
            ForumThread.title.ilike(f"%{search}%"),
            ForumThread.body.ilike(f"%{search}%"),
        ))

    total = (await db.execute(select(func.count()).select_from(ForumThread).where(and_(*conditions)))).scalar()
    items = (await db.execute(
        select(ForumThread).where(and_(*conditions))
        .order_by(ForumThread.is_pinned.desc(), desc(ForumThread.created_at))
        .limit(pagination.limit).offset(pagination.offset)
    )).scalars().all()

    return PaginatedResponse.build(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.post("/threads", response_model=ThreadResponse, status_code=201)
async def create_thread(
    data: ThreadCreate,
    current_user: User = Depends(require_permission(Permission.FORUM_CREATE_THREAD)),
    db: AsyncSession = Depends(get_db),
):
    thread = ForumThread(
        title=data.title,
        body=data.body,
        category=data.category,
        author_id=current_user.id,
        department_id=data.department_id,
        tags=data.tags or [],
        is_announcement=data.is_announcement,
        last_activity_at=datetime.now(timezone.utc).isoformat(),
    )
    db.add(thread)
    await db.flush()
    await db.refresh(thread)
    return thread


@router.get("/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: UUID,
    current_user: User = Depends(require_permission(Permission.FORUM_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    thread = (await db.execute(select(ForumThread).where(ForumThread.id == thread_id, ForumThread.is_deleted == False))).scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    # Increment view count
    thread.view_count += 1
    await db.flush()
    return thread


@router.post("/threads/{thread_id}/comments", response_model=CommentResponse, status_code=201)
async def add_comment(
    thread_id: UUID,
    data: CommentCreate,
    current_user: User = Depends(require_permission(Permission.FORUM_COMMENT)),
    db: AsyncSession = Depends(get_db),
):
    thread = (await db.execute(select(ForumThread).where(ForumThread.id == thread_id, ForumThread.is_deleted == False))).scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    if thread.is_locked:
        raise HTTPException(status_code=400, detail="Thread is locked")

    comment = ForumComment(
        thread_id=thread_id,
        author_id=current_user.id,
        body=data.body,
        parent_comment_id=data.parent_comment_id,
    )
    db.add(comment)
    thread.comment_count += 1
    thread.last_activity_at = datetime.now(timezone.utc).isoformat()
    await db.flush()
    await db.refresh(comment)
    return comment


@router.get("/threads/{thread_id}/comments", response_model=list[CommentResponse])
async def list_comments(
    thread_id: UUID,
    current_user: User = Depends(require_permission(Permission.FORUM_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ForumComment)
        .where(ForumComment.thread_id == thread_id, ForumComment.is_deleted == False)
        .order_by(ForumComment.created_at.asc())
    )
    return result.scalars().all()


@router.patch("/threads/{thread_id}/pin", status_code=204)
async def pin_thread(
    thread_id: UUID,
    current_user: User = Depends(require_permission(Permission.FORUM_PIN_THREAD)),
    db: AsyncSession = Depends(get_db),
):
    thread = (await db.execute(select(ForumThread).where(ForumThread.id == thread_id))).scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    thread.is_pinned = not thread.is_pinned
    await db.flush()
