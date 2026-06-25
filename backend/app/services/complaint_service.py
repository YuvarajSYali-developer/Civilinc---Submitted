"""
CivilInc Complaint Service
Business logic for complaint lifecycle management.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.complaint_repository import ComplaintRepository
from app.repositories.user_repository import UserRepository
from app.schemas.complaint import ComplaintCreate, ComplaintUpdate, ComplaintFeedback
from app.models.complaint import Complaint
from app.models.user import User
from app.core.permissions import Role
from app.core.config import settings


class ComplaintService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.complaint_repo = ComplaintRepository(db)
        self.user_repo = UserRepository(db)

    async def create_complaint(self, data: ComplaintCreate, citizen: User) -> Complaint:
        complaint_number = await self.complaint_repo.get_next_number()

        obj = data.model_dump()
        obj["complaint_number"] = complaint_number
        obj["citizen_id"] = citizen.id
        obj["status"] = "pending"

        # Calculate SLA due date (default 72h)
        sla_hours = 72
        obj["sla_due_at"] = (datetime.now(timezone.utc) + timedelta(hours=sla_hours)).isoformat()

        complaint = await self.complaint_repo.create(obj)

        # Log creation
        await self.complaint_repo.add_history({
            "complaint_id": complaint.id,
            "actor_id": citizen.id,
            "action": "created",
            "new_status": "pending",
            "comment": "Complaint submitted by citizen",
        })

        return complaint

    async def update_complaint(
        self, complaint_id: UUID, data: ComplaintUpdate, actor: User
    ) -> Complaint:
        complaint = await self.complaint_repo.get_by_id(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found")

        # Citizens can only update their own
        if actor.role == Role.CITIZEN and complaint.citizen_id != actor.id:
            raise PermissionError("You can only update your own complaints")

        updates = {k: v for k, v in data.model_dump().items() if v is not None}
        comment = updates.pop("comment", None)

        prev_status = complaint.status
        prev_priority = complaint.priority

        # Status transitions
        if "status" in updates and updates["status"] == "resolved":
            updates["resolved_at"] = datetime.now(timezone.utc).isoformat()
            start = complaint.created_at
            end = datetime.now(timezone.utc)
            updates["actual_resolution_days"] = (end - start).days

        updated = await self.complaint_repo.update(complaint, updates)

        # Record history
        action_parts = []
        if "status" in updates and updates["status"] != prev_status:
            action_parts.append("status_changed")
        if "priority" in updates:
            action_parts.append("priority_changed")
        if "assigned_officer_id" in updates:
            action_parts.append("assigned")

        action = "_".join(action_parts) if action_parts else "updated"

        await self.complaint_repo.add_history({
            "complaint_id": complaint.id,
            "actor_id": actor.id,
            "action": action,
            "previous_status": prev_status,
            "new_status": updates.get("status", prev_status),
            "previous_priority": prev_priority,
            "new_priority": updates.get("priority", prev_priority),
            "comment": comment,
        })

        return updated

    async def submit_feedback(
        self, complaint_id: UUID, data: ComplaintFeedback, citizen: User
    ) -> Complaint:
        complaint = await self.complaint_repo.get_by_id(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found")
        if complaint.citizen_id != citizen.id:
            raise PermissionError("You can only rate your own complaints")
        if complaint.status not in ("resolved", "closed"):
            raise ValueError("Can only rate resolved or closed complaints")

        updated = await self.complaint_repo.update(complaint, {
            "citizen_rating": data.rating,
            "citizen_feedback": data.feedback,
            "feedback_submitted_at": datetime.now(timezone.utc).isoformat(),
        })
        await self.complaint_repo.add_history({
            "complaint_id": complaint.id,
            "actor_id": citizen.id,
            "action": "feedback_submitted",
            "comment": f"Rating: {data.rating}/5. {data.feedback or ''}",
        })
        return updated

    async def apply_ai_predictions(self, complaint: Complaint, predictions: dict) -> Complaint:
        return await self.complaint_repo.update(complaint, {
            "ai_predicted_category": predictions.get("category"),
            "ai_predicted_priority": predictions.get("priority"),
            "ai_predicted_resolution_days": predictions.get("resolution_days"),
            "ai_confidence_score": predictions.get("confidence"),
            "ai_cluster_id": predictions.get("cluster_id"),
            "ai_processed": True,
            # Auto-assign AI predictions if not overridden
            "category": predictions.get("category", complaint.category),
            "priority": predictions.get("priority", complaint.priority),
        })
