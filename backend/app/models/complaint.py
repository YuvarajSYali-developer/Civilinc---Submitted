"""
CivilInc Complaint Model
Citizen complaints with AI classification, priority, and workflow.
"""
import uuid
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, Integer, Float, Enum as SAEnum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.department import Department
    from app.models.complaint_history import ComplaintHistory
    from app.models.notification import Notification


class ComplaintStatus(str):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class ComplaintPriority(str):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplaintCategory(str):
    ROADS = "roads"
    WATER_SUPPLY = "water_supply"
    DRAINAGE = "drainage"
    ELECTRICITY = "electricity"
    PARKS = "parks"
    BUILDINGS = "buildings"
    SANITATION = "sanitation"
    TRANSPORTATION = "transportation"
    OTHER = "other"


class Complaint(BaseModel):
    __tablename__ = "complaints"

    __table_args__ = (
        Index("ix_complaints_status_priority", "status", "priority"),
        Index("ix_complaints_ward_category", "ward_number", "category"),
        Index("ix_complaints_citizen_status", "citizen_id", "status"),
        Index("ix_complaints_department_status", "department_id", "status"),
    )

    # ─── Complaint Content ──────────────────────────────────────────────────────
    complaint_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    sub_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ─── Status & Priority ──────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(30), default="pending", nullable=False, index=True
    )
    priority: Mapped[str] = mapped_column(
        String(20), default="medium", nullable=False, index=True
    )

    # ─── Location ───────────────────────────────────────────────────────────────
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ward_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    zone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    latitude: Mapped[Optional[float]] = mapped_column(nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(nullable=True)
    pin_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)

    # ─── Relationships (FK) ─────────────────────────────────────────────────────
    citizen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_officer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ─── AI Predictions ─────────────────────────────────────────────────────────
    ai_predicted_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ai_predicted_priority: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ai_predicted_resolution_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ai_confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_cluster_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    ai_processed: Mapped[bool] = mapped_column(default=False, nullable=False)
    ai_override: Mapped[bool] = mapped_column(default=False, nullable=False)

    # ─── Resolution ─────────────────────────────────────────────────────────────
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    actual_resolution_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # ─── SLA Tracking ───────────────────────────────────────────────────────────
    sla_due_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sla_breached: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)

    # ─── Citizen Feedback ───────────────────────────────────────────────────────
    citizen_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    citizen_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    feedback_submitted_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # ─── Media Attachments ──────────────────────────────────────────────────────
    attachments: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True, default=list)

    # ─── Source Tracking ────────────────────────────────────────────────────────
    source: Mapped[str] = mapped_column(
        String(30), default="web", nullable=False  # web | mobile | whatsapp | ivr
    )
    escalation_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    escalated_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    duplicate_of_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ─── Relationships ───────────────────────────────────────────────────────────
    citizen: Mapped["User"] = relationship(
        "User", back_populates="complaints_filed", foreign_keys=[citizen_id]
    )
    department: Mapped[Optional["Department"]] = relationship(
        "Department", back_populates="complaints"
    )
    assigned_officer: Mapped[Optional["User"]] = relationship(
        "User", back_populates="complaints_assigned", foreign_keys=[assigned_officer_id]
    )
    history: Mapped[List["ComplaintHistory"]] = relationship(
        "ComplaintHistory", back_populates="complaint", lazy="select",
        order_by="ComplaintHistory.created_at.asc()"
    )

    def __repr__(self) -> str:
        return f"<Complaint {self.complaint_number} [{self.status}]>"
