"""
CivilInc Monitoring Utilities
Health checks, Prometheus metrics, structured logging.
"""
import time
import structlog
from fastapi import APIRouter
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

logger = structlog.get_logger("civilinc.monitoring")
router = APIRouter(tags=["Monitoring"])

# ── Prometheus Metrics ──────────────────────────────────────────────────────
REQUEST_COUNT = Counter("civilinc_http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("civilinc_http_request_duration_seconds", "HTTP request latency", ["endpoint"])
ACTIVE_WS = Gauge("civilinc_websocket_connections", "Active WebSocket connections")
AI_PREDICTIONS = Counter("civilinc_ai_predictions_total", "AI predictions made", ["system"])
COMPLAINTS_CREATED = Counter("civilinc_complaints_created_total", "Complaints created", ["category"])
PROJECTS_UPDATED = Counter("civilinc_projects_updated_total", "Project updates")

@router.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@router.get("/health/detailed")
async def detailed_health():
    from app.db.base import engine
    from app.ai.inference import _models
    db_ok = False
    try:
        async with engine.connect() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
            db_ok = True
    except: pass
    return {
        "status": "healthy" if db_ok else "degraded",
        "components": {
            "database": "ok" if db_ok else "error",
            "ai_models": f"{len(_models)} loaded",
        },
        "timestamp": time.time(),
    }
