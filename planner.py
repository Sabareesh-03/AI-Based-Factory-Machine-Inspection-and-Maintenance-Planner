"""
Pydantic schemas for AI Planner and Heuristic Priority API.
"""

from typing import List
from pydantic import BaseModel


class PriorityMachineOut(BaseModel):
    rank: int
    machine_id: int
    machine_code: str
    machine_name: str
    risk_level: str
    priority_score: float
    heuristic_score: float
    maintenance_duration: int
    required_skill: str
    reason: str


class PriorityListResponse(BaseModel):
    total_machines: int
    prioritized_queue: List[PriorityMachineOut]
