"""
CivilInc Department Model
Municipal departments owning projects and complaints.
"""
import uuid
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, Integer, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.project import Project
    from app.models.complaint import Complaint


class DepartmentStatus(str):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MERGED = "merged"


class Department(BaseModel):
    __tablename__ = "departments"

    # ─── Identity ───────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # ─── Hierarchy ──────────────────────────────────────────────────────────────
    parent_department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # ─── Head of Department ─────────────────────────────────────────────────────
    head_officer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ─── Contact & Location ─────────────────────────────────────────────────────
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    office_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # ─── Budget ─────────────────────────────────────────────────────────────────
    annual_budget: Mapped[Optional[float]] = mapped_column(nullable=True)
    budget_utilized: Mapped[float] = mapped_column(default=0.0, nullable=False)

    # ─── Operational Metadata ───────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False, index=True)
    complaint_categories: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True, default=list)
    sla_hours: Mapped[int] = mapped_column(Integer, default=72, nullable=False)  # default 3-day SLA
    
    # ─── Performance Metrics (denormalized for fast queries) ────────────────────
    total_complaints: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    resolved_complaints: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_projects: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active_projects: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ─── Relationships ───────────────────────────────────────────────────────────
    members: Mapped[List["User"]] = relationship(
        "User", back_populates="department", foreign_keys="User.department_id", lazy="select"
    )
    head_officer: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[head_officer_id], lazy="select"
    )
    projects: Mapped[List["Project"]] = relationship(
        "Project", back_populates="department", lazy="select"
    )
    complaints: Mapped[List["Complaint"]] = relationship(
        "Complaint", back_populates="department", lazy="select"
    )
    sub_departments: Mapped[List["Department"]] = relationship(
        "Department",
        foreign_keys=[parent_department_id],
        back_populates="parent_department",
        lazy="select",
    )
    parent_department: Mapped[Optional["Department"]] = relationship(
        "Department",
        foreign_keys=[parent_department_id],
        back_populates="sub_departments",
        remote_side="Department.id",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Department {self.code}: {self.name}>"
