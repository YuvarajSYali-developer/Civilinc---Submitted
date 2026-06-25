"""
CivilInc Analytics Endpoints
Citywide, departmental, and ward-level analytics.
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, text

from app.db.base import get_db
from app.core.dependencies import get_current_user, require_permission
from app.core.permissions import Permission
from app.models.user import User
from app.models.complaint import Complaint
from app.models.project import Project
from app.models.department import Department

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview")
async def citywide_overview(
    current_user: User = Depends(require_permission(Permission.ANALYTICS_VIEW_CITYWIDE)),
    db: AsyncSession = Depends(get_db),
):
    """High-level KPIs for the commissioner dashboard."""
    total_complaints = (await db.execute(select(func.count(Complaint.id)).where(Complaint.is_deleted == False))).scalar()
    pending_complaints = (await db.execute(select(func.count(Complaint.id)).where(Complaint.status == "pending", Complaint.is_deleted == False))).scalar()
    resolved_complaints = (await db.execute(select(func.count(Complaint.id)).where(Complaint.status == "resolved", Complaint.is_deleted == False))).scalar()
    critical_complaints = (await db.execute(select(func.count(Complaint.id)).where(Complaint.priority == "critical", Complaint.is_deleted == False))).scalar()
    sla_breached = (await db.execute(select(func.count(Complaint.id)).where(Complaint.sla_breached == True, Complaint.is_deleted == False))).scalar()

    total_projects = (await db.execute(select(func.count(Project.id)).where(Project.is_deleted == False))).scalar()
    active_projects = (await db.execute(select(func.count(Project.id)).where(Project.status == "in_progress", Project.is_deleted == False))).scalar()
    at_risk_projects = (await db.execute(select(func.count(Project.id)).where(Project.delay_probability >= 0.7, Project.is_deleted == False))).scalar()

    total_budget = (await db.execute(select(func.sum(Project.approved_budget)).where(Project.is_deleted == False))).scalar() or 0
    actual_cost = (await db.execute(select(func.sum(Project.actual_cost)).where(Project.is_deleted == False))).scalar() or 0

    return {
        "complaints": {
            "total": total_complaints,
            "pending": pending_complaints,
            "resolved": resolved_complaints,
            "critical": critical_complaints,
            "sla_breached": sla_breached,
            "resolution_rate": round((resolved_complaints / total_complaints * 100) if total_complaints else 0, 1),
        },
        "projects": {
            "total": total_projects,
            "active": active_projects,
            "at_risk": at_risk_projects,
            "total_budget": total_budget,
            "actual_cost": actual_cost,
            "budget_utilization_pct": round((actual_cost / total_budget * 100) if total_budget else 0, 1),
        },
    }


@router.get("/complaints/by-category")
async def complaints_by_category(
    current_user: User = Depends(require_permission(Permission.ANALYTICS_VIEW_DEPARTMENT)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Complaint.category, func.count(Complaint.id).label("count"))
        .where(Complaint.is_deleted == False)
        .group_by(Complaint.category)
        .order_by(desc("count"))
    )
    return [{"category": r.category, "count": r.count} for r in result.all()]


@router.get("/complaints/by-status")
async def complaints_by_status(
    current_user: User = Depends(require_permission(Permission.ANALYTICS_VIEW_DEPARTMENT)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Complaint.status, func.count(Complaint.id).label("count"))
        .where(Complaint.is_deleted == False)
        .group_by(Complaint.status)
    )
    return [{"status": r.status, "count": r.count} for r in result.all()]


@router.get("/complaints/by-ward")
async def complaints_by_ward(
    limit: int = Query(20, le=100),
    current_user: User = Depends(require_permission(Permission.ANALYTICS_VIEW_DEPARTMENT)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Complaint.ward_number, func.count(Complaint.id).label("count"))
        .where(Complaint.is_deleted == False, Complaint.ward_number != None)
        .group_by(Complaint.ward_number)
        .order_by(desc("count"))
        .limit(limit)
    )
    return [{"ward": r.ward_number, "count": r.count} for r in result.all()]


@router.get("/projects/by-status")
async def projects_by_status(
    current_user: User = Depends(require_permission(Permission.ANALYTICS_VIEW_DEPARTMENT)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project.status, func.count(Project.id).label("count"))
        .where(Project.is_deleted == False)
        .group_by(Project.status)
    )
    return [{"status": r.status, "count": r.count} for r in result.all()]


@router.get("/departments/performance")
async def department_performance(
    current_user: User = Depends(require_permission(Permission.ANALYTICS_VIEW_CITYWIDE)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            Department.id, Department.name, Department.code,
            Department.total_complaints, Department.resolved_complaints,
            Department.total_projects, Department.active_projects,
            Department.annual_budget, Department.budget_utilized,
            Department.sla_hours,
        ).where(Department.is_deleted == False, Department.status == "active")
        .order_by(Department.name)
    )
    rows = result.all()
    return [{
        "id": str(r.id),
        "name": r.name,
        "code": r.code,
        "total_complaints": r.total_complaints,
        "resolved_complaints": r.resolved_complaints,
        "resolution_rate": round((r.resolved_complaints / r.total_complaints * 100) if r.total_complaints else 0, 1),
        "total_projects": r.total_projects,
        "active_projects": r.active_projects,
        "annual_budget": r.annual_budget,
        "budget_utilized": r.budget_utilized,
    } for r in rows]
