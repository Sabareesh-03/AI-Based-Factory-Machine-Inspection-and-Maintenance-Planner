"""
AIPlan and AIPlanTask Models
Stores AI-generated maintenance plans and their individual tasks.
Will be populated by AI engine in later steps.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base


class AIPlanStatus:
    DRAFT    = "Draft"
    ACTIVE   = "Active"
    EXECUTED = "Executed"
    ARCHIVED = "Archived"
    ALL = [DRAFT, ACTIVE, EXECUTED, ARCHIVED]


class AIPlan(Base):
    __tablename__ = "ai_plans"

    id = Column(Integer, primary_key=True, index=True)

    # Plan Metadata
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    algorithm    = Column(String(100), nullable=True)    # e.g. "A*", "CSP+Backtracking"
    total_cost   = Column(Float, default=0.0)
    status       = Column(String(50), default=AIPlanStatus.DRAFT)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ── Relationships ──────────────────────────────────────────────────────────
    tasks = relationship("AIPlanTask", back_populates="plan",
                         cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AIPlan #{self.id} | {self.algorithm} | {self.status}>"


class AIPlanTask(Base):
    __tablename__ = "ai_plan_tasks"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    plan_id       = Column(Integer, ForeignKey("ai_plans.id",    ondelete="CASCADE"),  nullable=False)
    machine_id    = Column(Integer, ForeignKey("machines.id",    ondelete="CASCADE"),  nullable=False)
    technician_id = Column(Integer, ForeignKey("technicians.id", ondelete="SET NULL"), nullable=True)

    # Scheduling
    scheduled_date   = Column(DateTime, nullable=True)
    start_time       = Column(String(10), nullable=True)
    duration_minutes = Column(Integer, default=60)

    # AI Fields
    priority  = Column(String(50), nullable=True)
    task_cost = Column(Float, default=0.0)

    # ── Relationships ──────────────────────────────────────────────────────────
    plan       = relationship("AIPlan",      back_populates="tasks")
    machine    = relationship("Machine")
    technician = relationship("Technician")

    def __repr__(self):
        return f"<AIPlanTask #{self.id} | Plan {self.plan_id} | Machine {self.machine_id}>"
