"""
CivilInc Rate Limiting Middleware
Sliding window rate limiting using Redis.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import time

from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-process rate limiter.
    For production, replace with Redis-backed sliding window.
    """
    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self._store: dict = {}

    async def dispatch(self, request: Request, call_next):
        # Skip health checks
        if request.url.path in ("/health", "/metrics", "/api/v1/health"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60

        # Clean old entries
        self._store[client_ip] = [
            t for t in self._store.get(client_ip, []) if t > window_start
        ]

        if len(self._store[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again in a moment."},
                headers={"Retry-After": "60"},
            )

        self._store[client_ip].append(now)
        return await call_next(request)
