"""
CivilInc AI Endpoints
Exposes all 7 AI systems via FastAPI.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.dependencies import get_current_user, require_permission
from app.core.permissions import Permission
from app.models.user import User
from app.ai.inference import predict_complaint, predict_project_risk

router = APIRouter(prefix="/ai", tags=["AI Services"])


class ComplaintTriageRequest(BaseModel):
    title: str
    description: str
    zone: Optional[str] = "Central"
    source: Optional[str] = "web"


class ProjectRiskRequest(BaseModel):
    category: str
    department: str
    completion_pct: float
    budget_utilization_pct: float
    elapsed_pct: float
    planned_duration_days: int
    pre_monsoon_start: int = 0
    start_delay_days: int = 0
    source_fund: str = "BBMP Own Funds"
    approved_budget_lakhs: float = 0.0
    actual_cost_lakhs: float = 0.0
    delay_days: float = 0.0


@router.post("/complaint/triage")
async def triage_complaint(
    req: ComplaintTriageRequest,
    current_user: User = Depends(require_permission(Permission.AI_PREDICT)),
):
    """Systems 1-4: Category + Priority + Resolution Time + Cluster."""
    result = predict_complaint(req.title, req.description, req.zone or "Central", req.source or "web")
    if "error" in result:
        raise HTTPException(status_code=503, detail=f"AI service error: {result['error']}")
    return result


@router.post("/project/risk")
async def project_risk(
    req: ProjectRiskRequest,
    current_user: User = Depends(require_permission(Permission.AI_PREDICT)),
):
    """Systems 5-6: Delay probability + Budget overrun prediction."""
    result = predict_project_risk(**req.model_dump())
    if "error" in result:
        raise HTTPException(status_code=503, detail=f"AI service error: {result['error']}")
    return result


@router.get("/ward-risk")
async def ward_risk_scores(
    current_user: User = Depends(require_permission(Permission.AI_VIEW_INSIGHTS)),
):
    """System 7: Ward risk scores for all 197 wards."""
    import pandas as pd
    from pathlib import Path
    try:
        path = Path(__file__).parents[5] / "ai" / "models" / "ward_risk_scores.csv"
        df = pd.read_csv(path)
        return df[["ward_number","risk_score","risk_category","total_complaints",
                    "sla_breach_rate","avg_delay_prob"]].to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/health")
async def ai_health(current_user: User = Depends(get_current_user)):
    """Check if AI models are loaded."""
    from app.ai.inference import _load, _models
    _load()
    return {
        "models_loaded": len(_models) > 0,
        "model_count": len(_models),
        "systems": ["category_classifier","priority_predictor","resolution_predictor",
                    "complaint_clustering","delay_predictor","overrun_predictor","ward_risk"],
    }
