from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID
from datetime import datetime


class DepartmentCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    annual_budget: Optional[float] = None
    sla_hours: int = 72
    complaint_categories: Optional[List[str]] = None


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    annual_budget: Optional[float] = None
    sla_hours: Optional[int] = None
    head_officer_id: Optional[UUID] = None
    status: Optional[str] = None
    complaint_categories: Optional[List[str]] = None


class DepartmentResponse(BaseModel):
    id: UUID
    name: str
    code: str
    description: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str
    annual_budget: Optional[float] = None
    budget_utilized: float
    sla_hours: int
    total_complaints: int
    resolved_complaints: int
    total_projects: int
    active_projects: int
    complaint_categories: Optional[List[str]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
