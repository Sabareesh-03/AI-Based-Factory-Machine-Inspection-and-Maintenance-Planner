"""
Machines Router
GET /api/machines — returns all machines from database
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database.db import get_db
from app.models.machine import Machine
from app.schemas.machine import MachineOut, MachineListResponse

router = APIRouter()


@router.get("/machines", response_model=MachineListResponse, summary="List All Machines")
def get_machines(
    status: Optional[str] = Query(None, description="Filter by status"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    section: Optional[str] = Query(None, description="Filter by factory section"),
    db: Session = Depends(get_db),
):
    """
    Returns all machines with their current sensor readings,
    status, and maintenance schedule information.
    """
    query = db.query(Machine)

    if status:
        query = query.filter(Machine.status == status)
    if risk_level:
        query = query.filter(Machine.risk_level == risk_level)
    if section:
        query = query.filter(Machine.factory_section == section)

    machines = query.order_by(Machine.priority_score.desc()).all()
    return MachineListResponse(total=len(machines), machines=machines)
