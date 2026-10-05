"""
Rules Management & Testing Router
==================================
API Endpoints:
  - GET    /api/rules              : List all knowledge-base rules
  - GET    /api/rules/{rule_id}     : Retrieve single rule
  - POST   /api/rules              : Create new rule
  - PUT    /api/rules/{rule_id}     : Update existing rule
  - PATCH  /api/rules/{rule_id}/toggle : Enable/disable rule
  - DELETE /api/rules/{rule_id}     : Delete non-system rule
  - POST   /api/rules/test         : Safe dry-run evaluation of rules against custom facts
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db

from app.models.rule import Rule
from ai_engine.rule_engine import knowledge_engine, RuleFact
from app.schemas.rule import (
    RuleOut, RuleCreate, RuleUpdate, RuleTestInput, TriggeredRuleDetailOut, RuleTestResultOut
)

router = APIRouter(prefix="/api/rules", tags=["Knowledge-Based Rule Management & Explainable AI"])


@router.get("", response_model=List[RuleOut])
def get_all_rules(db: Session = Depends(get_db)):
    """List all knowledge base rules."""
    return db.query(Rule).all()


@router.get("/{rule_id}", response_model=RuleOut)
def get_rule_by_id(rule_id: int, db: Session = Depends(get_db)):
    """Retrieve single rule by ID."""
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule ID {rule_id} not found")
    return rule


@router.post("", response_model=RuleOut)
def create_rule(rule_in: RuleCreate, db: Session = Depends(get_db)):
    """Create a new rule in the Knowledge Base."""
    new_rule = Rule(
        name=rule_in.rule_name,
        description=rule_in.description,
        condition=rule_in.condition_expr,
        action=rule_in.recommended_action,
        severity=rule_in.severity,
        enabled=rule_in.is_active,
    )
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return new_rule


@router.put("/{rule_id}", response_model=RuleOut)
def update_rule(rule_id: int, rule_in: RuleUpdate, db: Session = Depends(get_db)):
    """Update an existing rule."""
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule ID {rule_id} not found")

    mapping = {
        "rule_name": "name",
        "description": "description",
        "condition_expr": "condition",
        "recommended_action": "action",
        "severity": "severity",
        "is_active": "enabled"
    }
    for field, val in rule_in.dict(exclude_unset=True).items():
        if field in mapping:
            setattr(rule, mapping[field], val)

    db.commit()
    db.refresh(rule)
    return rule


@router.patch("/{rule_id}/toggle", response_model=RuleOut)
def toggle_rule(rule_id: int, db: Session = Depends(get_db)):
    """Enable or disable a rule in the Knowledge Base."""
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule ID {rule_id} not found")

    rule.enabled = not rule.enabled
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete a non-system rule."""
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule ID {rule_id} not found")

    if getattr(rule, "is_system_rule", False):
        raise HTTPException(
            status_code=400,
            detail=f"System rule '{rule.rule_name}' is protected and cannot be deleted."
        )

    db.delete(rule)
    db.commit()
    return {"message": f"Rule ID {rule_id} deleted successfully."}


@router.post("/test", response_model=RuleTestResultOut)
def test_knowledge_base(test_in: RuleTestInput, db: Session = Depends(get_db)):
    """
    Safely evaluate enabled Knowledge Base rules against custom sensor facts.
    Does NOT modify the database.
    """
    db_rules = db.query(Rule).filter(Rule.enabled == True).all()

    facts = RuleFact(
        temperature=test_in.temperature,
        vibration=test_in.vibration,
        pressure=test_in.pressure,
        runtime_hours=test_in.runtime_hours,
        overdue_days=test_in.overdue_days,
        status=test_in.status,
    )

    res = knowledge_engine.evaluate_knowledge_base(facts, db_rules)

    triggered_out = [
        TriggeredRuleDetailOut(
            rule_id=r.rule_id,
            rule_name=r.rule_name,
            condition=r.condition,
            observed_value=r.observed_value,
            threshold=r.threshold,
            parameter=r.parameter,
            severity=r.severity,
            action=r.action,
            explanation=r.explanation,
        )
        for r in res.triggered_rules
    ]

    return RuleTestResultOut(
        highest_severity=res.highest_severity,
        final_recommended_action=res.final_recommended_action,
        total_rules_evaluated=res.total_rules_evaluated,
        triggered_count=res.triggered_count,
        triggered_rules=triggered_out,
        explanation_summary=res.explanation_summary,
    )
