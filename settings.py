"""
Application Settings & Configuration
"""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseModel as BaseSettings


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────────────────────────
    APP_NAME: str = os.getenv("APP_NAME", "Factory Maintenance Planner")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1")

    # ── Server ────────────────────────────────────────────────────────────────
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # ── CORS ──────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",  # Vite default dev server
        "http://localhost:5174",  # Vite secondary dev server
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
        "*",
    ]

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./factory_maintenance.db")

    # ── AI Engine ─────────────────────────────────────────────────────────────
    AI_ENGINE_VERSION: str = os.getenv("AI_ENGINE_VERSION", "1.0.0")


settings = Settings()
