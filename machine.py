"""Pydantic schema for Machine API responses."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class MachineOut(BaseModel):
    id: int
    machine_code: str
    name: str
    machine_type: str
    factory_section: str
    status: str
    risk_level: str
    priority_score: float
    temperature: float
    vibration: float
    pressure: float
    runtime_hours: float
    required_skill: Optional[str]
    maintenance_duration: int
    last_maintenance_date: Optional[datetime]
    next_maintenance_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MachineListResponse(BaseModel):
    total: int
    machines: List[MachineOut]
