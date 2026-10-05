"""
Pydantic schemas for Knowledge-Based Rule Management and Testing API.
"""

from typing import List, Optional
from pydantic import BaseModel


class RuleOut(BaseModel):
    id: int
    rule_code: str
    rule_name: str
    description: Optional[str] = None
    parameter: str
    operator: str
    threshold_value: float
    condition_expr: str
    severity: str
    recommended_action: str
    is_active: bool
    is_system_rule: bool = False

    class Config:
        from_attributes = True


class RuleCreate(BaseModel):
    rule_code: str
    rule_name: str
    description: Optional[str] = None
    parameter: str
    operator: str
    threshold_value: float
    condition_expr: str
    severity: str
    recommended_action: str
    is_active: bool = True
    is_system_rule: bool = False


class RuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    description: Optional[str] = None
    parameter: Optional[str] = None
    operator: Optional[str] = None
    threshold_value: Optional[float] = None
    condition_expr: Optional[str] = None
    severity: Optional[str] = None
    recommended_action: Optional[str] = None
    is_active: Optional[bool] = None


class RuleTestInput(BaseModel):
    temperature: float = 0.0
    vibration: float = 0.0
    pressure: float = 0.0
    runtime_hours: float = 0.0
    overdue_days: int = 0
    status: str = "Operational"


class TriggeredRuleDetailOut(BaseModel):
    rule_id: Optional[int] = None
    rule_name: str
    condition: str
    observed_value: float
    threshold: float
    parameter: str
    severity: str
    action: str
    explanation: str


class RuleTestResultOut(BaseModel):
    highest_severity: str
    final_recommended_action: str
    total_rules_evaluated: int
    triggered_count: int
    triggered_rules: List[TriggeredRuleDetailOut]
    explanation_summary: str
