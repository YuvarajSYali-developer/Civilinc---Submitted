from typing import Optional, List
from pydantic import BaseModel, ConfigDict, field_validator
from uuid import UUID
from datetime import datetime


class ComplaintCreate(BaseModel):
    title: str
    description: str
    category: str
    sub_category: Optional[str] = None
    address: Optional[str] = None
    ward_number: Optional[str] = None
    zone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    pin_code: Optional[str] = None
    attachments: Optional[List[dict]] = None
    source: str = "web"

    @field_validator("title")
    @classmethod
    def title_min_length(cls, v):
        if len(v.strip()) < 10:
            raise ValueError("Title must be at least 10 characters")
        return v.strip()

    @field_validator("description")
    @classmethod
    def description_min_length(cls, v):
        if len(v.strip()) < 20:
            raise ValueError("Description must be at least 20 characters")
        return v.strip()


class ComplaintUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_officer_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    resolution_notes: Optional[str] = None
    comment: Optional[str] = None


class ComplaintFeedback(BaseModel):
    rating: int
    feedback: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def rating_range(cls, v):
        if not 1 <= v <= 5:
            raise ValueError("Rating must be between 1 and 5")
        return v


class ComplaintResponse(BaseModel):
    id: UUID
    complaint_number: str
    title: str
    description: str
    category: str
    sub_category: Optional[str] = None
    status: str
    priority: str
    address: Optional[str] = None
    ward_number: Optional[str] = None
    zone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    citizen_id: UUID
    department_id: Optional[UUID] = None
    assigned_officer_id: Optional[UUID] = None
    ai_predicted_category: Optional[str] = None
    ai_predicted_priority: Optional[str] = None
    ai_predicted_resolution_days: Optional[int] = None
    ai_confidence_score: Optional[float] = None
    ai_processed: bool = False
    sla_breached: bool
    sla_due_at: Optional[str] = None
    citizen_rating: Optional[int] = None
    source: str
    escalation_level: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComplaintHistoryResponse(BaseModel):
    id: UUID
    action: str
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    previous_priority: Optional[str] = None
    new_priority: Optional[str] = None
    comment: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
