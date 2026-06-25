from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID
from datetime import datetime
from app.core.permissions import Role


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Role = Role.CITIZEN
    phone: Optional[str] = None
    department_id: Optional[UUID] = None
    employee_id: Optional[str] = None
    designation: Optional[str] = None
    ward_number: Optional[str] = None
    zone: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    designation: Optional[str] = None
    bio: Optional[str] = None
    ward_number: Optional[str] = None
    zone: Optional[str] = None
    address: Optional[str] = None
    avatar_url: Optional[str] = None
    notification_settings: Optional[dict] = None
    preferences: Optional[dict] = None


class UserAdminUpdate(UserUpdate):
    role: Optional[Role] = None
    is_active: Optional[bool] = None
    department_id: Optional[UUID] = None
    employee_id: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: Role
    phone: Optional[str] = None
    department_id: Optional[UUID] = None
    employee_id: Optional[str] = None
    designation: Optional[str] = None
    avatar_url: Optional[str] = None
    ward_number: Optional[str] = None
    zone: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
