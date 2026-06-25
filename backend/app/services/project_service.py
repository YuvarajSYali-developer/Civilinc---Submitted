"""
CivilInc Project Service
Infrastructure project lifecycle management.
"""
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.models.project import Project
from app.models.user import User
from app.core.permissions import Role


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.project_repo = ProjectRepository(db)

    async def create_project(self, data: ProjectCreate, creator: User) -> Project:
        project_number = await self.project_repo.get_next_number()
        obj = data.model_dump()
        obj["project_number"] = project_number
        obj["status"] = "planning"
        obj["completion_percentage"] = 0.0
        obj["actual_cost"] = 0.0
        obj["budget_utilized_pct"] = 0.0
        return await self.project_repo.create(obj)

    async def update_project(self, project_id: UUID, data: ProjectUpdate, actor: User) -> Project:
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise ValueError("Project not found")

        # Engineers can only update their own projects
        if actor.role == Role.ENGINEER and project.project_manager_id != actor.id:
            raise PermissionError("You can only update projects you manage")

        updates = {k: v for k, v in data.model_dump().items() if v is not None}

        # Recalculate budget utilization
        if "actual_cost" in updates and project.approved_budget:
            budget = updates.get("approved_budget", project.approved_budget)
            if budget and budget > 0:
                updates["budget_utilized_pct"] = round(
                    (updates["actual_cost"] / budget) * 100, 2
                )

        return await self.project_repo.update(project, updates)

    async def get_at_risk_projects(self, threshold: float = 0.7) -> list[Project]:
        return await self.project_repo.get_at_risk(threshold)
