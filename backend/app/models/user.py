"""
CivilInc User Model
Officers, commissioners, coordinators, and citizens.
"""
import uuid
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel
from app.core.permissions import Role

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.complaint import Complaint
    from app.models.project import Project
    from app.models.notification import Notification
    from app.models.audit_log import AuditLog
    from app.models.forum import ForumThread, ForumComment


class User(BaseModel):
    __tablename__ = "users"

    # ─── Identity ───────────────────────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # ─── Profile ────────────────────────────────────────────────────────────────
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    employee_id: Mapped[Optional[str]] = mapped_column(
        String(50), unique=True, nullable=True, index=True
    )
    designation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ─── Role & Access ──────────────────────────────────────────────────────────
    role: Mapped[Role] = mapped_column(
        SAEnum(Role, name="user_role", create_type=True),
        nullable=False,
        default=Role.CITIZEN,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ─── Department Membership ──────────────────────────────────────────────────
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ─── Location ───────────────────────────────────────────────────────────────
    ward_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    zone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(nullable=True)

    # ─── Preferences ────────────────────────────────────────────────────────────
    preferences: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    notification_settings: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)

    # ─── Auth State ─────────────────────────────────────────────────────────────
    last_login_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    locked_until: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    password_changed_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # ─── Relationships ───────────────────────────────────────────────────────────
    department: Mapped[Optional["Department"]] = relationship(
        "Department", back_populates="members", foreign_keys=[department_id]
    )
    complaints_filed: Mapped[List["Complaint"]] = relationship(
        "Complaint",
        back_populates="citizen",
        foreign_keys="Complaint.citizen_id",
        lazy="select",
    )
    complaints_assigned: Mapped[List["Complaint"]] = relationship(
        "Complaint",
        back_populates="assigned_officer",
        foreign_keys="Complaint.assigned_officer_id",
        lazy="select",
    )
    projects_managed: Mapped[List["Project"]] = relationship(
        "Project",
        back_populates="project_manager",
        foreign_keys="Project.project_manager_id",
        lazy="select",
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="user", lazy="select"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="actor", lazy="select"
    )
    forum_threads: Mapped[List["ForumThread"]] = relationship(
        "ForumThread", back_populates="author", lazy="select"
    )
    forum_comments: Mapped[List["ForumComment"]] = relationship(
        "ForumComment", back_populates="author", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<User {self.email} [{self.role}]>"
