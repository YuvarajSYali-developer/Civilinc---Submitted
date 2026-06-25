from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime


class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: str
    planned_start_date: Optional[str] = None
    planned_end_date: Optional[str] = None
    estimated_cost: float = 0.0
    department_id: UUID
    project_manager_id: Optional[UUID] = None
    ward_number: Optional[str] = None
    zone: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_fund: Optional[str] = None
    tender_number: Optional[str] = None
    contractor_name: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: bool = True


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    phase: Optional[str] = None
    completion_percentage: Optional[float] = None
    actual_start_date: Optional[str] = None
    actual_end_date: Optional[str] = None
    actual_cost: Optional[float] = None
    approved_budget: Optional[float] = None
    project_manager_id: Optional[UUID] = None
    contractor_name: Optional[str] = None
    milestones: Optional[List[dict]] = None
    attachments: Optional[List[dict]] = None
    last_inspection_date: Optional[str] = None


class ProjectResponse(BaseModel):
    id: UUID
    project_number: str
    title: str
    description: Optional[str] = None
    category: str
    status: str
    phase: Optional[str] = None
    completion_percentage: float
    planned_start_date: Optional[str] = None
    planned_end_date: Optional[str] = None
    actual_start_date: Optional[str] = None
    estimated_cost: float
    approved_budget: Optional[float] = None
    actual_cost: float
    budget_utilized_pct: float
    department_id: UUID
    project_manager_id: Optional[UUID] = None
    ward_number: Optional[str] = None
    zone: Optional[str] = None
    delay_probability: Optional[float] = None
    overrun_probability: Optional[float] = None
    risk_score: Optional[float] = None
    risk_category: Optional[str] = None
    contractor_name: Optional[str] = None
    is_public: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
