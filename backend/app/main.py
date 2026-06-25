"""
CivilInc FastAPI Application — Production Grade
Main entry point with all middleware, routers, and lifecycle hooks.
"""
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1.router import api_router
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.utils.monitoring import router as monitoring_router

logger = structlog.get_logger("civilinc")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("CivilInc starting", version=settings.APP_VERSION, env=settings.APP_ENV)
    yield
    logger.info("CivilInc shutting down")


app = FastAPI(
    title="CivilInc API",
    description="Urban Infrastructure Intelligence Platform — BBMP Bengaluru",
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ─── Middleware ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_origin_regex=settings.BACKEND_CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time"],
)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.RATE_LIMIT_REQUESTS)

# ─── Routers ─────────────────────────────────────────────────────────────────
app.include_router(api_router)
app.include_router(monitoring_router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION, "environment": settings.APP_ENV}


@app.get("/", tags=["Root"])
async def root():
    return {"message": "CivilInc API", "docs": "/api/docs", "version": settings.APP_VERSION}


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(status_code=404, content={"detail": "Resource not found"})

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error("Unhandled exception", path=request.url.path, error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
