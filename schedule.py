"""
Pydantic schemas for CSP Maintenance Scheduling API.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class ScheduledTaskOut(BaseModel):
    machine_id: int
    machine_code: str
    machine_name: str
    risk_level: str
    priority_score: float
    heuristic_score: float
    technician_id: int
    technician_code: str
    technician_name: str
    date: str
    start_time: str
    end_time: str
    duration: int
    reason: str


class UnscheduledTaskOut(BaseModel):
    machine_id: int
    machine_code: str
    machine_name: str
    risk_level: str
    reason: str


class CSPScheduleResponse(BaseModel):
    status: str
    total_tasks: int
    scheduled_tasks_count: int
    unscheduled_tasks_count: int
    schedule_score: float
    constraint_summary: Dict[str, Any]
    scheduled_tasks: List[ScheduledTaskOut]
    unscheduled_tasks: List[UnscheduledTaskOut]
