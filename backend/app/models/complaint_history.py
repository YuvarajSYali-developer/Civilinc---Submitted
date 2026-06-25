"""
CivilInc Complaint History Model
Immutable audit trail for all complaint state changes.
"""
import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.models.complaint import Complaint
    from app.models.user import User


class ComplaintHistory(BaseModel):
    __tablename__ = "complaint_history"

    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ─── Change Details ─────────────────────────────────────────────────────────
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # e.g. status_changed | priority_changed | assigned | comment_added | escalated

    previous_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    new_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    previous_priority: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    new_priority: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    previous_officer_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_officer_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)

    # ─── Relationships ───────────────────────────────────────────────────────────
    complaint: Mapped["Complaint"] = relationship("Complaint", back_populates="history")
    actor: Mapped[Optional["User"]] = relationship("User", foreign_keys=[actor_id])

    def __repr__(self) -> str:
        return f"<ComplaintHistory {self.complaint_id} [{self.action}]>"
