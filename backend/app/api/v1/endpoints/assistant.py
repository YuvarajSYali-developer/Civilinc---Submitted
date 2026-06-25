"""
CivilInc Commissioner AI Assistant
Natural language queries over operational data — powered by Anthropic Claude API.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
import json

from app.db.base import get_db
from app.core.dependencies import require_permission
from app.core.permissions import Permission
from app.models.user import User
from app.models.complaint import Complaint
from app.models.project import Project
from app.models.department import Department

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])


class AssistantRequest(BaseModel):
    query: str
    context: dict = {}


async def build_context_snapshot(db: AsyncSession) -> dict:
    """Pull live operational metrics for the assistant prompt."""
    total_c = (await db.execute(select(func.count(Complaint.id)).where(Complaint.is_deleted == False))).scalar()
    pending_c = (await db.execute(select(func.count(Complaint.id)).where(Complaint.status == "pending", Complaint.is_deleted == False))).scalar()
    critical_c = (await db.execute(select(func.count(Complaint.id)).where(Complaint.priority == "critical", Complaint.is_deleted == False))).scalar()
    sla_breached = (await db.execute(select(func.count(Complaint.id)).where(Complaint.sla_breached == True, Complaint.is_deleted == False))).scalar()
    total_p = (await db.execute(select(func.count(Project.id)).where(Project.is_deleted == False))).scalar()
    at_risk_p = (await db.execute(select(func.count(Project.id)).where(Project.delay_probability >= 0.7, Project.is_deleted == False))).scalar()

    dept_stats = (await db.execute(
        select(Department.name, Department.code, Department.total_complaints,
               Department.resolved_complaints, Department.active_projects)
        .where(Department.is_deleted == False, Department.status == "active")
    )).all()

    return {
        "complaints": {"total": total_c, "pending": pending_c, "critical": critical_c, "sla_breached": sla_breached},
        "projects": {"total": total_p, "at_risk": at_risk_p},
        "departments": [
            {"name": d.name, "code": d.code, "total_complaints": d.total_complaints,
             "resolved_complaints": d.resolved_complaints, "active_projects": d.active_projects,
             "resolution_rate": round((d.resolved_complaints / d.total_complaints * 100) if d.total_complaints else 0, 1)}
            for d in dept_stats
        ]
    }


@router.post("/query")
async def query_assistant(
    req: AssistantRequest,
    current_user: User = Depends(require_permission(Permission.AI_VIEW_INSIGHTS)),
    db: AsyncSession = Depends(get_db),
):
    """Natural language query over live BBMP operational data."""
    try:
        import httpx
        snapshot = await build_context_snapshot(db)

        system_prompt = f"""You are the CivilInc AI Assistant for the Commissioner of Bruhat Bengaluru Mahanagara Palike (BBMP).
You have access to real-time operational data. Answer queries concisely and accurately.
Current operational snapshot:
{json.dumps(snapshot, indent=2)}

Guidelines:
- Be specific with numbers from the data
- Highlight critical issues proactively
- Use INR for budget figures
- Reference department names and codes
- Keep responses under 300 words unless a report is requested
- Format responses clearly with bullet points or sections as needed"""

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": "", "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 1000,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": req.query}]
                },
                timeout=30.0,
            )
        if resp.status_code != 200:
            # Fallback: answer from snapshot without Claude
            return _fallback_answer(req.query, snapshot)

        content = resp.json()["content"][0]["text"]
        return {"answer": content, "data_snapshot": snapshot, "model": "claude-sonnet-4-6"}

    except Exception as e:
        return _fallback_answer(req.query, await build_context_snapshot(db))


def _fallback_answer(query: str, snapshot: dict) -> dict:
    """Rule-based fallback when Claude API is unavailable."""
    q = query.lower()
    c = snapshot["complaints"]; p = snapshot["projects"]
    depts = snapshot["departments"]

    if "backlog" in q or "pending" in q:
        highest = max(depts, key=lambda d: d["total_complaints"] - d["resolved_complaints"], default=None)
        answer = f"Complaint Backlog Summary:\n• Total pending: {c['pending']:,}\n• Critical: {c['critical']:,}\n• SLA breached: {c['sla_breached']:,}"
        if highest:
            backlog = highest['total_complaints'] - highest['resolved_complaints']
            answer += f"\n• Highest backlog: {highest['name']} ({backlog:,} unresolved)"
    elif "delay" in q or "risk" in q or "project" in q:
        answer = f"Project Risk Summary:\n• Total projects: {p['total']:,}\n• At risk (>70% delay prob): {p['at_risk']:,}\n• Risk rate: {round(p['at_risk']/max(1,p['total'])*100,1)}%"
    elif "department" in q or "performance" in q:
        sorted_depts = sorted(depts, key=lambda d: d["resolution_rate"], reverse=True)
        answer = "Department Performance:\n"
        for d in sorted_depts[:5]:
            answer += f"• {d['name']}: {d['resolution_rate']}% resolution rate ({d['total_complaints']} complaints)\n"
    else:
        answer = (
            f"Current Status — BBMP Bengaluru:\n"
            f"• Complaints: {c['total']:,} total | {c['pending']:,} pending | {c['critical']:,} critical\n"
            f"• SLA Breached: {c['sla_breached']:,}\n"
            f"• Projects: {p['total']:,} total | {p['at_risk']:,} at risk\n"
            f"• Departments active: {len(depts)}"
        )
    return {"answer": answer, "data_snapshot": snapshot, "model": "fallback"}


@router.get("/report/weekly")
async def weekly_report(
    current_user: User = Depends(require_permission(Permission.REPORT_GENERATE)),
    db: AsyncSession = Depends(get_db),
):
    """Generate a structured weekly commissioner report."""
    snapshot = await build_context_snapshot(db)
    c = snapshot["complaints"]; p = snapshot["projects"]
    depts = snapshot["departments"]

    best_dept = max(depts, key=lambda d: d["resolution_rate"], default={"name":"N/A","resolution_rate":0})
    worst_dept = min(depts, key=lambda d: d["resolution_rate"], default={"name":"N/A","resolution_rate":0})

    report = {
        "title": "Weekly Commissioner Report — BBMP Bengaluru",
        "period": "Current Week",
        "executive_summary": {
            "total_complaints": c["total"],
            "pending": c["pending"],
            "critical": c["critical"],
            "sla_breach_count": c["sla_breached"],
            "projects_at_risk": p["at_risk"],
        },
        "highlights": {
            "best_performing_dept": best_dept["name"],
            "best_resolution_rate": f"{best_dept['resolution_rate']}%",
            "needs_attention": worst_dept["name"],
            "lowest_resolution_rate": f"{worst_dept['resolution_rate']}%",
        },
        "department_breakdown": depts,
        "recommendations": _generate_recommendations(snapshot),
    }
    return report


def _generate_recommendations(snapshot: dict) -> list[str]:
    recs = []
    c = snapshot["complaints"]; p = snapshot["projects"]; depts = snapshot["departments"]
    if c["sla_breached"] > 100:
        recs.append(f"⚠️ {c['sla_breached']} complaints have breached SLA. Immediate escalation required.")
    if c["critical"] > 50:
        recs.append(f"🚨 {c['critical']} critical complaints pending. Deploy additional resources.")
    if p["at_risk"] > 10:
        recs.append(f"🏗️ {p['at_risk']} projects at high delay risk. Review contractor performance.")
    for d in depts:
        if d["resolution_rate"] < 50 and d["total_complaints"] > 100:
            recs.append(f"📊 {d['name']} has {d['resolution_rate']}% resolution rate — below threshold.")
    if not recs:
        recs.append("✅ Operations within normal parameters. Continue monitoring SLA compliance.")
    return recs
