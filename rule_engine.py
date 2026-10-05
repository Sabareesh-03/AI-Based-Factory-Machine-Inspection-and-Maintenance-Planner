"""
Knowledge-Based Expert System Rule Engine
==========================================
Implements a Knowledge-Based Reasoning System with explicit Facts, Rules, Inference,
Conflict Resolution, and Explainable Diagnostic Reasoning.

Expert System Mapping:
---------------------
1. KNOWLEDGE BASE (KB):
   - Collection of production rules (IF condition THEN action & severity).
   - Loaded dynamically from database `Rule` table + built-in safety rules.

2. FACTS (F):
   - Working memory containing observed sensor parameters:
     F = { temperature, vibration, pressure, runtime_hours, status, overdue_days }

3. INFERENCE ENGINE:
   - Matches Facts F against Knowledge Base KB conditions.
   - Evaluates boolean expressions in a secure execution context.

4. CONFLICT RESOLUTION:
   - Resolves multiple triggered rules using Severity Hierarchy:
     Critical (Priority 4) > High (Priority 3) > Medium (Priority 2) > Low (Priority 1)
   - Derives final recommended action from the highest-priority triggered rule.

5. EXPLAINABILITY:
   - Generates trace explanation strings mapping Rule -> Condition -> Fact Observation -> Action.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple


@dataclass
class RuleFact:
    """Working Memory Fact containing machine parameter readings."""
    temperature: float = 0.0
    vibration: float = 0.0
    pressure: float = 0.0
    runtime_hours: float = 0.0
    overdue_days: int = 0
    status: str = "Operational"


@dataclass
class TriggeredRuleDetail:
    """Explanation breakdown of a triggered rule."""
    rule_id: Optional[int]
    rule_name: str
    condition: str
    observed_value: float
    threshold: float
    parameter: str
    severity: str
    action: str
    explanation: str


@dataclass
class InferenceResult:
    """Result of Knowledge-Based Inference & Conflict Resolution."""
    highest_severity: str
    final_recommended_action: str
    total_rules_evaluated: int
    triggered_count: int
    triggered_rules: List[TriggeredRuleDetail]
    explanation_summary: str


SEVERITY_HIERARCHY = {
    "Critical": 4,
    "High": 3,
    "Medium": 2,
    "Low": 1,
}

RECOMMENDED_ACTIONS = {
    "Critical": "Immediate Maintenance Required - Halt Operations",
    "High": "Schedule Priority Maintenance Within 24 Hours",
    "Medium": "Schedule Inspection & Calibration",
    "Low": "Continue Normal Monitoring",
}


class KnowledgeRuleEngine:
    """
    Expert System Inference Engine for Machine Diagnostics.
    """

    def _eval_condition(self, condition_str: str, facts: Dict[str, Any]) -> bool:
        """
        Safely evaluates boolean condition string against facts working memory.
        """
        try:
            # Safe evaluation context with only numeric machine facts
            safe_context = {
                "temperature": float(facts.get("temperature", 0.0)),
                "vibration": float(facts.get("vibration", 0.0)),
                "pressure": float(facts.get("pressure", 0.0)),
                "runtime_hours": float(facts.get("runtime_hours", 0.0)),
                "overdue_days": int(facts.get("overdue_days", 0)),
                "status": str(facts.get("status", "Operational")),
            }
            return bool(eval(condition_str, {"__builtins__": None}, safe_context))
        except Exception:
            return False

    def evaluate_knowledge_base(
        self,
        facts: RuleFact,
        db_rules: List[Any]
    ) -> InferenceResult:
        """
        Executes Inference Engine evaluation across enabled rules in Knowledge Base.
        """
        facts_dict = {
            "temperature": facts.temperature,
            "vibration": facts.vibration,
            "pressure": facts.pressure,
            "runtime_hours": facts.runtime_hours,
            "overdue_days": facts.overdue_days,
            "status": facts.status,
        }

        triggered_details: List[TriggeredRuleDetail] = []
        enabled_rules = [r for r in db_rules if getattr(r, "is_active", True) or getattr(r, "enabled", True)]

        for rule in enabled_rules:
            cond = rule.condition_expr if hasattr(rule, "condition_expr") else getattr(rule, "condition", "")
            if not cond:
                continue

            if self._eval_condition(cond, facts_dict):
                param = getattr(rule, "parameter", "sensor")
                threshold = float(getattr(rule, "threshold_value", 0.0) or 0.0)
                observed = float(facts_dict.get(param, 0.0))
                severity = getattr(rule, "severity", "Medium")
                action = getattr(rule, "recommended_action", None) or getattr(rule, "action", "Inspect machine")
                rule_name = getattr(rule, "rule_name", None) or getattr(rule, "name", "Threshold Violation Rule")

                explanation_msg = (
                    f"Rule '{rule_name}' triggered because {param} = {observed:.2f}, "
                    f"violating condition ({cond}). Recommended action: {action}."
                )

                triggered_details.append(
                    TriggeredRuleDetail(
                        rule_id=getattr(rule, "id", None),
                        rule_name=rule_name,
                        condition=cond,
                        observed_value=observed,
                        threshold=threshold,
                        parameter=param,
                        severity=severity,
                        action=action,
                        explanation=explanation_msg,
                    )
                )

        # ── CONFLICT RESOLUTION ────────────────────────────────────────────────
        if not triggered_details:
            highest_sev = "Low"
            final_action = RECOMMENDED_ACTIONS["Low"]
            summary = "Knowledge Base Evaluation: All machine parameters operating within normal safety limits."
        else:
            # Sort triggered rules by severity rank descending
            triggered_details.sort(
                key=lambda r: SEVERITY_HIERARCHY.get(r.severity, 1),
                reverse=True
            )
            highest_sev = triggered_details[0].severity
            final_action = RECOMMENDED_ACTIONS.get(highest_sev, triggered_details[0].action)
            
            reasons_str = "; ".join([r.explanation for r in triggered_details])
            summary = f"Knowledge Base Conflict Resolution: Identified {highest_sev} severity tier. {reasons_str}"

        return InferenceResult(
            highest_severity=highest_sev,
            final_recommended_action=final_action,
            total_rules_evaluated=len(enabled_rules),
            triggered_count=len(triggered_details),
            triggered_rules=triggered_details,
            explanation_summary=summary,
        )


# Singleton instance
knowledge_engine = KnowledgeRuleEngine()
