"""
Technicians Router
GET /api/technicians — returns all technicians from database
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database.db import get_db
from app.models.technician import Technician
from app.schemas.technician import TechnicianOut, TechnicianListResponse

router = APIRouter()


@router.get("/technicians", response_model=TechnicianListResponse, summary="List All Technicians")
def get_technicians(
    availability: Optional[str] = Query(None, description="Filter by availability status"),
    db: Session = Depends(get_db),
):
    """
    Returns all technicians with their skills, availability,
    and current workload information.
    """
    query = db.query(Technician)

    if availability:
        query = query.filter(Technician.availability_status == availability)

    technicians = query.order_by(Technician.technician_code).all()
    return TechnicianListResponse(total=len(technicians), technicians=technicians)
