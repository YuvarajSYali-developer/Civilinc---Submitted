"""
CivilInc API v1 Router
Aggregates all endpoint routers.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, users, departments, complaints, projects, forum, notifications, analytics, gis
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(departments.router)
api_router.include_router(complaints.router)
api_router.include_router(projects.router)
api_router.include_router(forum.router)
api_router.include_router(notifications.router)
api_router.include_router(analytics.router)
api_router.include_router(gis.router)

from app.api.v1.endpoints import ai
api_router.include_router(ai.router)
from app.api.v1.endpoints import websocket as ws_module
api_router.include_router(ws_module.router)
from app.api.v1.endpoints import assistant
api_router.include_router(assistant.router)
