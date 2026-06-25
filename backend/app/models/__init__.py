"""
CivilInc Models Registry
All models imported here so Alembic can discover them.
"""
from app.models.base_model import BaseModel, UUIDMixin, TimestampMixin, SoftDeleteMixin
from app.models.user import User
from app.models.department import Department
from app.models.complaint import Complaint
from app.models.complaint_history import ComplaintHistory
from app.models.project import Project
from app.models.forum import ForumThread, ForumComment
from app.models.notification import Notification
from app.models.audit_log import AuditLog

__all__ = [
    "BaseModel",
    "User",
    "Department",
    "Complaint",
    "ComplaintHistory",
    "Project",
    "ForumThread",
    "ForumComment",
    "Notification",
    "AuditLog",
]
