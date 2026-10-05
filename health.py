"""
Health Check Router
GET /api/health
"""

from fastapi import APIRouter
from datetime import datetime, timezone
from app.config.settings import settings

router = APIRouter()


@router.get("/health", summary="Health Check")
async def health_check():
    """
    Returns the current health status of the API server.
    Used by the frontend and monitoring systems to verify backend availability.
    """
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ai_engine_version": settings.AI_ENGINE_VERSION,
        "database": "connected",
    }
