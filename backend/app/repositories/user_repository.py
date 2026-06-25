from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email.lower(), User.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def get_by_employee_id(self, employee_id: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.employee_id == employee_id, User.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def get_officers_by_department(self, department_id) -> list[User]:
        from app.core.permissions import Role
        result = await self.db.execute(
            select(User).where(
                User.department_id == department_id,
                User.role.in_([Role.ENGINEER, Role.COORDINATOR]),
                User.is_active == True,
                User.is_deleted == False,
            )
        )
        return result.scalars().all()
