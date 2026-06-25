"""
CivilInc Forum Models
Discussion threads and comments for interdepartmental collaboration.
"""
import uuid
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, Integer, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.department import Department


class ForumThread(BaseModel):
    __tablename__ = "forum_threads"

    __table_args__ = (
        Index("ix_forum_threads_dept_pinned", "department_id", "is_pinned"),
        Index("ix_forum_threads_category", "category"),
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # general | infrastructure | complaint | budget | announcement | emergency

    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True
    )

    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_announcement: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    upvotes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tags: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True, default=list)
    attachments: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True, default=list)
    last_activity_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    author: Mapped["User"] = relationship("User", back_populates="forum_threads", foreign_keys=[author_id])
    department: Mapped[Optional["Department"]] = relationship("Department", foreign_keys=[department_id])
    comments: Mapped[List["ForumComment"]] = relationship(
        "ForumComment", back_populates="thread", lazy="select",
        order_by="ForumComment.created_at.asc()"
    )


class ForumComment(BaseModel):
    __tablename__ = "forum_comments"

    __table_args__ = (
        Index("ix_forum_comments_thread", "thread_id"),
    )

    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("forum_threads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    parent_comment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("forum_comments.id", ondelete="SET NULL"), nullable=True
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    upvotes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_solution: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    attachments: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True, default=list)

    thread: Mapped["ForumThread"] = relationship("ForumThread", back_populates="comments")
    author: Mapped["User"] = relationship("User", back_populates="forum_comments", foreign_keys=[author_id])
    replies: Mapped[List["ForumComment"]] = relationship(
        "ForumComment", foreign_keys=[parent_comment_id],
        back_populates="parent_comment", lazy="select"
    )
    parent_comment: Mapped[Optional["ForumComment"]] = relationship(
        "ForumComment", foreign_keys=[parent_comment_id],
        back_populates="replies", remote_side="ForumComment.id"
    )
