"""Dashboard aggregated statistics schema."""

from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_machines: int
    operational: int
    warning: int
    critical: int
    under_maintenance: int
    offline: int
    total_technicians: int
    available_technicians: int
    busy_technicians: int
    active_alerts: int
    critical_alerts: int
    pending_tasks: int
    scheduled_tasks: int
