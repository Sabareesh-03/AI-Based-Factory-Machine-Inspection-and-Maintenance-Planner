"""
Pydantic schemas for AI Planner Orchestration API.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.schemas.planner import PriorityMachineOut
from app.schemas.schedule import ScheduledTaskOut, UnscheduledTaskOut


class FullPlanRunResponse(BaseModel):
    status: str
    timestamp: str
    total_machines: int
    machines_requiring_attention: int
    critical_count: int
    high_risk_count: int
    scheduled_task_count: int
    unscheduled_task_count: int
    prioritized_machines: List[PriorityMachineOut]
    generated_schedule: List[ScheduledTaskOut]
    unscheduled_tasks: List[UnscheduledTaskOut]
    schedule_score: float
    explanation: str
