"""
Pydantic schemas for Machine Inspection and Risk Analysis API.
"""

from typing import List, Optional
from pydantic import BaseModel


class RuleMatchOut(BaseModel):
    rule_id: Optional[int] = None
    rule_name: str
    parameter: str
    operator: str
    threshold: float
    actual_value: float
    severity: str
    message: str
    weight: float = 1.0


class InspectionResultOut(BaseModel):
    machine_id: int
    machine_code: str
    machine_name: str
    machine_type: str
    factory_section: str
    status: str
    
    # Readings
    temperature: float
    vibration: float
    pressure: float
    runtime_hours: float
    
    # Engine analysis
    risk_level: str
    priority_score: float
    recommended_action: str
    
    # Matches and explanation
    matched_rules: List[RuleMatchOut]
    explanation: List[str]
    alert_created: bool
    alert_message: Optional[str] = None


class BatchInspectionSummary(BaseModel):
    total_inspected: int
    low_count: int
    medium_count: int
    high_count: int
    critical_count: int
    alerts_created: int
    results: List[InspectionResultOut]
