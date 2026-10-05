"""
Pydantic schemas for Dynamic Re-Planning API.
"""

from typing import List, Optional
from pydantic import BaseModel
from app.schemas.schedule import ScheduledTaskOut


class ReplanRequest(BaseModel):
    trigger_type: str  # "machine_risk_change", "technician_unavailability", "new_critical_machine", "machine_offline"
    machine_id: Optional[int] = None
    new_risk_level: Optional[str] = None
    new_machine_status: Optional[str] = None
    technician_id: Optional[int] = None
    new_availability_status: Optional[str] = None


class ScheduleChangeItem(BaseModel):
    machine_id: int
    machine_code: str
    machine_name: str
    change_type: str
    previous_technician: Optional[str] = None
    new_technician: Optional[str] = None
    previous_slot: Optional[str] = None
    new_slot: Optional[str] = None
    reason: str


class DynamicReplanResponse(BaseModel):
    trigger: str
    detected_change: str
    affected_task_ids: List[int]
    previous_schedule: List[ScheduledTaskOut]
    revised_schedule: List[ScheduledTaskOut]
    changes: List[ScheduleChangeItem]
    explanation: str
