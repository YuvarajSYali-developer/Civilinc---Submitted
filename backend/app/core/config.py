"""
CivilInc Core Configuration
Production-grade settings with environment variable support.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator, PostgresDsn
from typing import Optional, List, Union
import secrets


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── Application ────────────────────────────────────────────────────────────
    APP_NAME: str = "CivilInc"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"  # development | staging | production
    DEBUG: bool = False
    SECRET_KEY: str = secrets.token_urlsafe(64)
    API_V1_STR: str = "/api/v1"
    ALLOWED_HOSTS: List[str] = ["*"]

    # ─── Database ───────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://civilinc:civilinc_dev@localhost:5432/civilinc"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_ECHO: bool = False

    # ─── Redis ──────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1 hour default

    # ─── Authentication ─────────────────────────────────────────────────────────
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1
    MIN_PASSWORD_LENGTH: int = 8

    # ─── CORS ───────────────────────────────────────────────────────────────────
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://127.0.0.1:3000",
        "http://127.0.0.1:4173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:4173",
        "http://localhost:5173",
        "null",
        "https://civilinc.vercel.app",
    ]
    BACKEND_CORS_ORIGIN_REGEX: str = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

    # ─── Rate Limiting ──────────────────────────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    AUTH_RATE_LIMIT_REQUESTS: int = 10
    AUTH_RATE_LIMIT_WINDOW: int = 60

    # ─── Email ──────────────────────────────────────────────────────────────────
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@civilinc.gov.in"
    EMAIL_FROM_NAME: str = "CivilInc Platform"

    # ─── File Storage ───────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "pdf", "doc", "docx"]

    # ─── AI / ML ────────────────────────────────────────────────────────────────
    AI_MODEL_DIR: str = "/app/ai/models"
    AI_CONFIDENCE_THRESHOLD: float = 0.65

    # ─── GIS ────────────────────────────────────────────────────────────────────
    DEFAULT_MAP_CENTER_LAT: float = 12.9716  # Bengaluru
    DEFAULT_MAP_CENTER_LNG: float = 77.5946
    DEFAULT_MAP_ZOOM: int = 11

    # ─── Pagination ─────────────────────────────────────────────────────────────
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # ─── WebSocket ──────────────────────────────────────────────────────────────
    WS_HEARTBEAT_INTERVAL: int = 30

    # ─── Monitoring ─────────────────────────────────────────────────────────────
    ENABLE_METRICS: bool = True
    LOG_LEVEL: str = "INFO"

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_flag(cls, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "development"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "production"}:
                return False
        return value


settings = Settings()
