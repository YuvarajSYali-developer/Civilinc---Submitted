"""
CivilInc Project Model
Infrastructure projects with lifecycle tracking, budget, and AI risk scores.
"""
import uuid
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, Integer, Float, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.department import Department


class Project(BaseModel):
    __tablename__ = "projects"

    __table_args__ = (
        Index("ix_projects_status_dept", "status", "department_id"),
        Index("ix_projects_ward_status", "ward_number", "status"),
    )

    # ─── Identity ───────────────────────────────────────────────────────────────
    project_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # ─── Status & Phase ─────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(30), default="planning", nullable=False, index=True
        # planning | tendering | in_progress | on_hold | completed | cancelled
    )
    phase: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    completion_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # ─── Timeline ───────────────────────────────────────────────────────────────
    planned_start_date: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    planned_end_date: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, index=True)
    actual_start_date: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    actual_end_date: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    last_inspection_date: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # ─── Budget ─────────────────────────────────────────────────────────────────
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    approved_budget: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    budget_utilized_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # ─── Location ───────────────────────────────────────────────────────────────
    ward_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    zone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(nullable=True)
    geojson_geometry: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # ─── Ownership ──────────────────────────────────────────────────────────────
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    project_manager_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    contractor_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contractor_contact: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ─── AI Risk Assessment ─────────────────────────────────────────────────────
    delay_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    overrun_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    expected_overrun_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    risk_category: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ai_last_assessed: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # ─── Metadata ───────────────────────────────────────────────────────────────
    attachments: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True, default=list)
    milestones: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True, default=list)
    tags: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True, default=list)
    source_fund: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tender_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_public: Mapped[bool] = mapped_column(default=True, nullable=False)

    # ─── Relationships ───────────────────────────────────────────────────────────
    department: Mapped["Department"] = relationship("Department", back_populates="projects")
    project_manager: Mapped[Optional["User"]] = relationship(
        "User", back_populates="projects_managed", foreign_keys=[project_manager_id]
    )

    def __repr__(self) -> str:
        return f"<Project {self.project_number}: {self.title[:40]}>"
