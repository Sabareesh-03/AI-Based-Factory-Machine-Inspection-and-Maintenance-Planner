"""Pydantic schema for Alert API responses."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class AlertOut(BaseModel):
    id: int
    machine_id: int
    severity: str
    message: str
    recommended_action: Optional[str]
    status: str
    read_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    total: int
    alerts: List[AlertOut]
