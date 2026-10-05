"""Pydantic schema for Technician API responses."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class TechnicianOut(BaseModel):
    id: int
    technician_code: str
    name: str
    department: str
    skills: str
    experience_level: str
    availability_status: str
    working_hours_start: str
    working_hours_end: str
    maximum_daily_tasks: int
    current_workload: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TechnicianListResponse(BaseModel):
    total: int
    technicians: List[TechnicianOut]
