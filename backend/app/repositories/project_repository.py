from typing import Optional
from uuid import UUID
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.project import Project
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db: AsyncSession):
        super().__init__(Project, db)

    async def get_by_number(self, project_number: str) -> Optional[Project]:
        result = await self.db.execute(
            select(Project).where(
                Project.project_number == project_number,
                Project.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_next_number(self) -> str:
        result = await self.db.execute(select(func.count(Project.id)))
        count = result.scalar() or 0
        return f"PRJ-{str(count + 1).zfill(6)}"

    async def get_at_risk(self, delay_threshold: float = 0.7) -> list[Project]:
        result = await self.db.execute(
            select(Project).where(
                Project.delay_probability >= delay_threshold,
                Project.status.in_(["in_progress", "planning", "tendering"]),
                Project.is_deleted == False,
            ).order_by(desc(Project.delay_probability))
        )
        return result.scalars().all()
