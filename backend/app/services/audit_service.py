"""
CivilInc Audit Service
Records all significant system actions for compliance.
"""
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        action: str,
        entity_type: str,
        actor_id: Optional[UUID] = None,
        entity_id: Optional[str] = None,
        description: Optional[str] = None,
        before_state: Optional[dict] = None,
        after_state: Optional[dict] = None,
        changed_fields: Optional[list] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> AuditLog:
        log = AuditLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            description=description,
            before_state=before_state,
            after_state=after_state,
            changed_fields=changed_fields,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            metadata=metadata or {},
        )
        self.db.add(log)
        await self.db.flush()
        return log
