from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.complaint import Complaint
from app.models.complaint_history import ComplaintHistory
from app.repositories.base import BaseRepository


class ComplaintRepository(BaseRepository[Complaint]):
    def __init__(self, db: AsyncSession):
        super().__init__(Complaint, db)

    async def get_by_number(self, complaint_number: str) -> Optional[Complaint]:
        result = await self.db.execute(
            select(Complaint).where(
                Complaint.complaint_number == complaint_number,
                Complaint.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_citizen(self, citizen_id: UUID, limit=20, offset=0):
        result = await self.db.execute(
            select(Complaint)
            .where(Complaint.citizen_id == citizen_id, Complaint.is_deleted == False)
            .order_by(desc(Complaint.created_at))
            .limit(limit).offset(offset)
        )
        return result.scalars().all()

    async def add_history(self, history_data: dict) -> ComplaintHistory:
        h = ComplaintHistory(**history_data)
        self.db.add(h)
        await self.db.flush()
        return h

    async def get_department_stats(self, department_id: UUID) -> dict:
        result = await self.db.execute(
            select(
                Complaint.status,
                func.count(Complaint.id).label("count")
            ).where(
                Complaint.department_id == department_id,
                Complaint.is_deleted == False,
            ).group_by(Complaint.status)
        )
        rows = result.all()
        return {row.status: row.count for row in rows}

    async def get_next_number(self) -> str:
        result = await self.db.execute(select(func.count(Complaint.id)))
        count = result.scalar() or 0
        return f"CMP-{str(count + 1).zfill(7)}"
