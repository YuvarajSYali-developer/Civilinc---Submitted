"""
CivilInc GIS Endpoints
Geospatial data for map visualisation layers.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.base import get_db
from app.core.dependencies import get_current_user
from app.core.permissions import Permission, Role, has_permission
from app.models.user import User
from app.models.complaint import Complaint
from app.models.project import Project

router = APIRouter(prefix="/gis", tags=["GIS"])


@router.get("/complaints/points")
async def complaint_points(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    ward_number: Optional[str] = Query(None),
    limit: int = Query(500, le=5000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """GeoJSON FeatureCollection of complaint locations for map rendering."""
    conditions = [
        Complaint.is_deleted == False,
        Complaint.latitude != None,
        Complaint.longitude != None,
    ]
    if current_user.role == Role.CITIZEN:
        conditions.append(Complaint.citizen_id == current_user.id)
    if status:
        conditions.append(Complaint.status == status)
    if category:
        conditions.append(Complaint.category == category)
    if ward_number:
        conditions.append(Complaint.ward_number == ward_number)

    result = await db.execute(
        select(
            Complaint.id, Complaint.complaint_number, Complaint.title,
            Complaint.category, Complaint.status, Complaint.priority,
            Complaint.latitude, Complaint.longitude, Complaint.ward_number,
            Complaint.created_at,
        ).where(and_(*conditions)).limit(limit)
    )
    rows = result.all()

    features = [{
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [r.longitude, r.latitude]},
        "properties": {
            "id": str(r.id),
            "complaint_number": r.complaint_number,
            "title": r.title,
            "category": r.category,
            "status": r.status,
            "priority": r.priority,
            "ward_number": r.ward_number,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        },
    } for r in rows]

    return {"type": "FeatureCollection", "features": features, "total": len(features)}


@router.get("/projects/points")
async def project_points(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    limit: int = Query(500, le=5000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """GeoJSON FeatureCollection of project locations."""
    conditions = [
        Project.is_deleted == False,
        Project.latitude != None,
        Project.longitude != None,
    ]
    if current_user.role == Role.CITIZEN:
        conditions.append(Project.is_public == True)
    if status:
        conditions.append(Project.status == status)
    if category:
        conditions.append(Project.category == category)

    result = await db.execute(
        select(
            Project.id, Project.project_number, Project.title,
            Project.category, Project.status, Project.completion_percentage,
            Project.delay_probability, Project.risk_score, Project.risk_category,
            Project.latitude, Project.longitude, Project.ward_number,
        ).where(and_(*conditions)).limit(limit)
    )
    rows = result.all()

    features = [{
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [r.longitude, r.latitude]},
        "properties": {
            "id": str(r.id),
            "project_number": r.project_number,
            "title": r.title,
            "category": r.category,
            "status": r.status,
            "completion_percentage": r.completion_percentage,
            "delay_probability": r.delay_probability,
            "risk_score": r.risk_score,
            "risk_category": r.risk_category,
            "ward_number": r.ward_number,
        },
    } for r in rows]

    return {"type": "FeatureCollection", "features": features, "total": len(features)}


@router.get("/heatmap/complaints")
async def complaint_heatmap(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lat/lng intensity data for complaint density heatmap."""
    conditions = [
        Complaint.is_deleted == False,
        Complaint.latitude != None,
        Complaint.longitude != None,
    ]
    result = await db.execute(
        select(Complaint.latitude, Complaint.longitude, Complaint.priority)
        .where(and_(*conditions)).limit(10000)
    )
    priority_weights = {"low": 1, "medium": 2, "high": 3, "critical": 5}
    points = [
        [r.latitude, r.longitude, priority_weights.get(r.priority, 1)]
        for r in result.all()
    ]
    return {"points": points, "total": len(points)}
