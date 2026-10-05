"""
Alerts Router
GET /api/alerts — returns all alerts from database
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database.db import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertOut, AlertListResponse

router = APIRouter()


@router.get("/alerts", response_model=AlertListResponse, summary="List All Alerts")
def get_alerts(
    status: Optional[str] = Query(None, description="Filter by status (Unread/Read/Resolved)"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    db: Session = Depends(get_db),
):
    """
    Returns all system alerts, ordered by severity and creation time.
    """
    query = db.query(Alert)

    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)

    alerts = query.order_by(Alert.created_at.desc()).all()
    return AlertListResponse(total=len(alerts), alerts=alerts)
