"""
MaintenanceTask Model
Represents a scheduled or pending maintenance task.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base


class TaskStatus:
    PENDING      = "Pending"
    SCHEDULED    = "Scheduled"
    IN_PROGRESS  = "In Progress"
    COMPLETED    = "Completed"
    RESCHEDULED  = "Rescheduled"
    CANCELLED    = "Cancelled"
    ALL = [PENDING, SCHEDULED, IN_PROGRESS, COMPLETED, RESCHEDULED, CANCELLED]


class TaskPriority:
    LOW      = "Low"
    MEDIUM   = "Medium"
    HIGH     = "High"
    CRITICAL = "Critical"
    ALL = [LOW, MEDIUM, HIGH, CRITICAL]


class MaintenanceTask(Base):
    __tablename__ = "maintenance_tasks"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    machine_id    = Column(Integer, ForeignKey("machines.id",    ondelete="CASCADE"), nullable=False)
    technician_id = Column(Integer, ForeignKey("technicians.id", ondelete="SET NULL"), nullable=True)

    # Scheduling
    scheduled_date   = Column(DateTime, nullable=True)
    start_time       = Column(String(10), nullable=True)    # "HH:MM"
    duration_minutes = Column(Integer,   default=60)

    # Classification
    priority = Column(String(50), default=TaskPriority.MEDIUM)
    status   = Column(String(50), default=TaskStatus.PENDING)
    reason   = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)

    # ── Relationships ──────────────────────────────────────────────────────────
    machine    = relationship("Machine",    back_populates="maintenance_tasks")
    technician = relationship("Technician", back_populates="maintenance_tasks")

    def __repr__(self):
        return f"<MaintenanceTask #{self.id} | Machine {self.machine_id} | {self.status}>"
