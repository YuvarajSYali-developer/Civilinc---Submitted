"""
CivilInc Base Repository
Generic async CRUD operations using SQLAlchemy 2.0.
"""
from typing import Generic, TypeVar, Type, Optional, List, Tuple, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base_model import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        result = await self.db.execute(
            select(self.model).where(
                self.model.id == id,
                self.model.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        filters: Optional[List] = None,
        order_by=None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[ModelType], int]:
        conditions = [self.model.is_deleted == False]
        if filters:
            conditions.extend(filters)

        count_q = select(func.count()).select_from(self.model).where(and_(*conditions))
        total_result = await self.db.execute(count_q)
        total = total_result.scalar()

        q = select(self.model).where(and_(*conditions))
        if order_by is not None:
            q = q.order_by(order_by)
        else:
            q = q.order_by(desc(self.model.created_at))
        q = q.limit(limit).offset(offset)

        result = await self.db.execute(q)
        return result.scalars().all(), total

    async def create(self, obj_in: dict) -> ModelType:
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: ModelType, updates: dict) -> ModelType:
        for field, value in updates.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db_obj.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def soft_delete(self, db_obj: ModelType) -> ModelType:
        db_obj.soft_delete()
        await self.db.flush()
        return db_obj

    async def count(self, filters: Optional[List] = None) -> int:
        conditions = [self.model.is_deleted == False]
        if filters:
            conditions.extend(filters)
        result = await self.db.execute(
            select(func.count()).select_from(self.model).where(and_(*conditions))
        )
        return result.scalar()
