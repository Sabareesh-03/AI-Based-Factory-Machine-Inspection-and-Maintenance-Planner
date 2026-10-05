"""
MaintenanceHistory Model
Records completed maintenance activities.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base


class MaintenanceHistory(Base):
    __tablename__ = "maintenance_history"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    machine_id    = Column(Integer, ForeignKey("machines.id",    ondelete="CASCADE"), nullable=False)
    technician_id = Column(Integer, ForeignKey("technicians.id", ondelete="SET NULL"), nullable=True)

    # Record
    maintenance_date = Column(DateTime, nullable=False)
    issue            = Column(Text, nullable=False)
    action_taken     = Column(Text, nullable=False)
    duration_minutes = Column(Integer, default=60)
    notes            = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ── Relationships ──────────────────────────────────────────────────────────
    machine    = relationship("Machine",    back_populates="maintenance_history")
    technician = relationship("Technician", back_populates="maintenance_history")

    def __repr__(self):
        return f"<MaintenanceHistory #{self.id} | Machine {self.machine_id} | {self.maintenance_date}>"
