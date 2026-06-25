"""
CivilInc Common Schemas
Shared response shapes, pagination, and error models.
"""
from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, field_validator, ConfigDict
from uuid import UUID
from datetime import datetime

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int
    has_next: bool
    has_prev: bool

    @classmethod
    def build(cls, items: List[T], total: int, page: int, page_size: int) -> "PaginatedResponse[T]":
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1,
        )


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    errors: Optional[List[str]] = None

    @classmethod
    def ok(cls, data: T = None, message: str = None) -> "APIResponse[T]":
        return cls(success=True, data=data, message=message)

    @classmethod
    def fail(cls, message: str, errors: List[str] = None) -> "APIResponse":
        return cls(success=False, message=message, errors=errors or [])


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None
    errors: Optional[List[dict]] = None


class TimestampSchema(BaseModel):
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UUIDSchema(BaseModel):
    id: UUID

    model_config = ConfigDict(from_attributes=True)
