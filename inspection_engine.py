"""
Rule-Based Machine Inspection Engine
=====================================
Implements Knowledge-Based / Rule-Based Reasoning for machine condition analysis.

Architecture:
  1. Built-in threshold rules (always evaluated — no DB dependency)
  2. Dynamic DB rules (loaded from Rule table, evaluated via safe expression eval)
  3. Risk aggregation → final risk level + priority score
  4. Explainable output → human-readable explanation of WHY a machine is classified

This engine does NOT use Machine Learning.
All decisions are fully transparent and explainable.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


# ── Risk & Recommendation Constants ──────────────────────────────────────────
RISK_LEVELS = ["Low", "Medium", "High", "Critical"]

RISK_RANK = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}

RISK_BASE_SCORE = {"Low": 5.0, "Medium": 28.0, "High": 58.0, "Critical": 88.0}

RECOMMENDATIONS = {
    "Low":      "Continue Monitoring",
    "Medium":   "Schedule Inspection",
    "High":     "Schedule Maintenance Soon",
    "Critical": "Immediate Maintenance Required",
}

# ── Built-in Parameter Thresholds ────────────────────────────────────────────
# These always run regardless of DB rules.
# They serve as a safety baseline.

BUILTIN_RULES = [
    # Temperature rules
    {
        "name":      "Critical Temperature",
        "condition": "temperature > 90",
        "severity":  "Critical",
        "message":   "Temperature {val:.1f}°C exceeds critical threshold (90°C).",
        "param":     "temperature",
        "op":        "gt",
        "threshold": 90,
    },
    {
        "name":      "High Temperature",
        "condition": "temperature > 75",
        "severity":  "High",
        "message":   "Temperature {val:.1f}°C is high (threshold: 75°C).",
        "param":     "temperature",
        "op":        "gt",
        "threshold": 75,
    },
    {
        "name":      "Elevated Temperature",
        "condition": "temperature > 65",
        "severity":  "Medium",
        "message":   "Temperature {val:.1f}°C is elevated (threshold: 65°C).",
        "param":     "temperature",
        "op":        "gt",
        "threshold": 65,
    },
    # Vibration rules
    {
        "name":      "Critical Vibration",
        "condition": "vibration > 10.0",
        "severity":  "Critical",
        "message":   "Vibration {val:.2f} mm/s exceeds critical threshold (10.0 mm/s).",
        "param":     "vibration",
        "op":        "gt",
        "threshold": 10.0,
    },
    {
        "name":      "High Vibration",
        "condition": "vibration > 7.0",
        "severity":  "High",
        "message":   "Vibration {val:.2f} mm/s is dangerously high (threshold: 7.0 mm/s).",
        "param":     "vibration",
        "op":        "gt",
        "threshold": 7.0,
    },
    {
        "name":      "Elevated Vibration",
        "condition": "vibration > 4.5",
        "severity":  "Medium",
        "message":   "Vibration {val:.2f} mm/s is above normal (threshold: 4.5 mm/s).",
        "param":     "vibration",
        "op":        "gt",
        "threshold": 4.5,
    },
    # Pressure rules
    {
        "name":      "Critical Pressure",
        "condition": "pressure > 25",
        "severity":  "Critical",
        "message":   "Pressure {val:.1f} bar exceeds critical safety limit (25 bar).",
        "param":     "pressure",
        "op":        "gt",
        "threshold": 25,
    },
    {
        "name":      "High Pressure",
        "condition": "pressure > 20",
        "severity":  "High",
        "message":   "Pressure {val:.1f} bar is high (threshold: 20 bar).",
        "param":     "pressure",
        "op":        "gt",
        "threshold": 20,
    },
    {
        "name":      "Elevated Pressure",
        "condition": "pressure > 15",
        "severity":  "Medium",
        "message":   "Pressure {val:.1f} bar is above normal (threshold: 15 bar).",
        "param":     "pressure",
        "op":        "gt",
        "threshold": 15,
    },
    # Runtime rules
    {
        "name":      "Very High Runtime",
        "condition": "runtime_hours > 10000",
        "severity":  "High",
        "message":   "Runtime {val:.0f} hours exceeds high-maintenance threshold (10,000 hrs).",
        "param":     "runtime_hours",
        "op":        "gt",
        "threshold": 10000,
    },
    {
        "name":      "High Runtime",
        "condition": "runtime_hours > 7000",
        "severity":  "Medium",
        "message":   "Runtime {val:.0f} hours is high (threshold: 7,000 hrs). Service recommended.",
        "param":     "runtime_hours",
        "op":        "gt",
        "threshold": 7000,
    },
]


# ── Data Classes for Inspection Results ──────────────────────────────────────
@dataclass
class TriggeredRule:
    rule_id:   Optional[int]
    rule_name: str
    condition: str
    severity:  str
    triggered_message: str
    is_builtin: bool = True


@dataclass
class InspectionResult:
    # Machine identity
    machine_id:      int
    machine_code:    str
    machine_name:    str
    machine_type:    str
    factory_section: str

    # Sensor readings at inspection time
    status:        str
    temperature:   float
    vibration:     float
    pressure:      float
    runtime_hours: float

    # Analysis output
    triggered_rules:    List[TriggeredRule] = field(default_factory=list)
    risk_level:         str   = "Low"
    previous_risk_level:str   = "Low"
    priority_score:     float = 0.0
    recommended_action: str   = "Continue Monitoring"
    explanation:        str   = ""

    # Alert tracking
    alert_generated: bool          = False
    alert_id:        Optional[int] = None
    alert_severity:  Optional[str] = None

    # Meta
    inspected_at: datetime = field(default_factory=datetime.utcnow)

    def as_dict(self) -> dict:
        return {
            "machine_id":        self.machine_id,
            "machine_code":      self.machine_code,
            "machine_name":      self.machine_name,
            "machine_type":      self.machine_type,
            "factory_section":   self.factory_section,
            "status":            self.status,
            "temperature":       self.temperature,
            "vibration":         self.vibration,
            "pressure":          self.pressure,
            "runtime_hours":     self.runtime_hours,
            "triggered_rules": [
                {
                    "rule_id":          r.rule_id,
                    "rule_name":        r.rule_name,
                    "condition":        r.condition,
                    "severity":         r.severity,
                    "triggered_message":r.triggered_message,
                    "is_builtin":       r.is_builtin,
                }
                for r in self.triggered_rules
            ],
            "risk_level":          self.risk_level,
            "previous_risk_level": self.previous_risk_level,
            "priority_score":      self.priority_score,
            "recommended_action":  self.recommended_action,
            "explanation":         self.explanation,
            "alert_generated":     self.alert_generated,
            "alert_id":            self.alert_id,
            "alert_severity":      self.alert_severity,
            "inspected_at":        self.inspected_at.isoformat(),
        }


# ── Machine Context for DB Rule Evaluation ────────────────────────────────────
class _MachineContext:
    """Provides safe attribute access for eval() of DB rule conditions."""

    def __init__(self, machine):
        self.temperature          = machine.temperature or 0.0
        self.vibration            = machine.vibration   or 0.0
        self.pressure             = machine.pressure    or 0.0
        self.runtime_hours        = machine.runtime_hours or 0.0
        self.status               = machine.status
        self.risk_level           = machine.risk_level
        self.next_maintenance_date = machine.next_maintenance_date
        self.last_maintenance_date = machine.last_maintenance_date
        self.priority_score       = machine.priority_score or 0.0


def _safe_eval(condition: str, context: dict) -> bool:
    """
    Safely evaluate a rule condition string.
    Only allows machine attributes and datetime builtins.
    All exceptions are caught — a failing rule is treated as non-triggered.
    """
    safe_globals = {"__builtins__": {}}
    try:
        return bool(eval(condition, safe_globals, context))   # noqa: S307
    except Exception:
        return False


# ── Core Inspection Engine ────────────────────────────────────────────────────
class MachineInspectionEngine:
    """
    Knowledge-Based Rule Engine for machine condition analysis.

    Evaluation order:
      1. Built-in threshold rules (always active)
      2. Dynamic rules loaded from the Rule database table
      3. Aggregate worst severity → final risk level
      4. Compute priority score with modifiers
      5. Build human-readable explanation
    """

    # ── Built-in Rule Evaluation ───────────────────────────────────────────────
    def _evaluate_builtin_rules(self, machine) -> List[TriggeredRule]:
        """Evaluate hard-coded parameter threshold rules."""
        triggered: List[TriggeredRule] = []
        params = {
            "temperature":  machine.temperature or 0.0,
            "vibration":    machine.vibration   or 0.0,
            "pressure":     machine.pressure    or 0.0,
            "runtime_hours":machine.runtime_hours or 0.0,
        }

        for rule in BUILTIN_RULES:
            param_val = params.get(rule["param"], 0.0)
            if rule["op"] == "gt" and param_val > rule["threshold"]:
                triggered.append(TriggeredRule(
                    rule_id=None,
                    rule_name=rule["name"],
                    condition=rule["condition"],
                    severity=rule["severity"],
                    triggered_message=rule["message"].format(val=param_val),
                    is_builtin=True,
                ))

        return triggered

    # ── DB Rule Evaluation ─────────────────────────────────────────────────────
    def _evaluate_db_rules(self, machine, db_rules) -> List[TriggeredRule]:
        """Evaluate rules loaded from the Rule database table."""
        triggered: List[TriggeredRule] = []
        if not db_rules:
            return triggered

        ctx_obj  = _MachineContext(machine)
        now_val  = datetime.utcnow()
        eval_ctx = {
            "machine":      ctx_obj,
            "temperature":  ctx_obj.temperature,
            "vibration":    ctx_obj.vibration,
            "pressure":     ctx_obj.pressure,
            "runtime_hours":ctx_obj.runtime_hours,
            "status":       ctx_obj.status,
            "now":          lambda: now_val,
            "datetime":     datetime,
        }

        for rule in db_rules:
            if not rule.enabled:
                continue
            if _safe_eval(rule.condition, eval_ctx):
                triggered.append(TriggeredRule(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    condition=rule.condition,
                    severity=rule.severity,
                    triggered_message=(
                        f"[DB Rule] {rule.name}: {rule.description or rule.condition}"
                    ),
                    is_builtin=False,
                ))

        return triggered

    # ── Risk Aggregation ───────────────────────────────────────────────────────
    def _aggregate_risk(self, triggered: List[TriggeredRule]) -> str:
        """Return the highest risk level among all triggered rules."""
        if not triggered:
            return "Low"
        worst = max(triggered, key=lambda r: RISK_RANK.get(r.severity, 0))
        return worst.severity

    # ── Overdue Modifier ───────────────────────────────────────────────────────
    def _overdue_days(self, machine) -> int:
        if machine.next_maintenance_date:
            delta = datetime.utcnow() - machine.next_maintenance_date
            return max(0, delta.days)
        return 0

    # ── Priority Score Calculation ─────────────────────────────────────────────
    def _calculate_priority_score(
        self,
        machine,
        risk_level: str,
        triggered: List[TriggeredRule],
    ) -> float:
        """
        Priority score 0–100.  Higher = more urgent.
        Base from risk level + parameter modifiers + overdue penalty.

        This score is used to order machines for future maintenance planning.
        The calculation is intentionally simple and auditable.
        """
        score = RISK_BASE_SCORE.get(risk_level, 5.0)

        # ── Temperature modifier ──────────────────────────────────────────────
        temp = machine.temperature or 0.0
        if   temp > 90: score += 10
        elif temp > 75: score += 6
        elif temp > 65: score += 3

        # ── Vibration modifier ────────────────────────────────────────────────
        vib = machine.vibration or 0.0
        if   vib > 10.0: score += 8
        elif vib > 7.0:  score += 5
        elif vib > 4.5:  score += 2

        # ── Pressure modifier ─────────────────────────────────────────────────
        pres = machine.pressure or 0.0
        if   pres > 25: score += 6
        elif pres > 20: score += 3
        elif pres > 15: score += 1

        # ── Runtime modifier ──────────────────────────────────────────────────
        rt = machine.runtime_hours or 0.0
        if   rt > 10000: score += 5
        elif rt > 7000:  score += 2

        # ── Overdue penalty ───────────────────────────────────────────────────
        overdue = self._overdue_days(machine)
        if overdue > 0:
            score += min(overdue * 1.5, 12)   # max +12 from overdue

        # ── Multiple trigger bonus ────────────────────────────────────────────
        critical_triggers = sum(1 for r in triggered if r.severity == "Critical")
        if critical_triggers >= 2:
            score += 5  # compound failure bonus

        return round(min(score, 100.0), 2)

    # ── Explanation Builder ────────────────────────────────────────────────────
    def _build_explanation(
        self,
        machine,
        risk_level: str,
        triggered: List[TriggeredRule],
        overdue_days: int,
    ) -> str:
        """
        Build a human-readable explanation of the inspection decision.
        Example: "Machine MCH-012 classified as Critical because:
                  temperature 95°C exceeded critical threshold (90°C);
                  vibration 12.5 mm/s exceeded critical threshold (10.0 mm/s)."
        """
        if not triggered:
            return (
                f"Machine {machine.machine_code} is operating within normal parameters. "
                f"No thresholds exceeded. Risk level: Low."
            )

        reasons = [r.triggered_message for r in triggered]
        overdue_note = (
            f" Additionally, maintenance is {overdue_days} day(s) overdue."
            if overdue_days > 0 else ""
        )

        reasons_str = "; ".join(reasons)
        return (
            f"Machine {machine.machine_code} classified as {risk_level} "
            f"because: {reasons_str}.{overdue_note}"
        )

    # ── Main Inspect Method ────────────────────────────────────────────────────
    def inspect(self, machine, db_rules=None) -> InspectionResult:
        """
        Perform a full rule-based inspection of a single machine.

        Parameters
        ----------
        machine  : SQLAlchemy Machine ORM object
        db_rules : list of Rule ORM objects (pass [] to skip DB rules)

        Returns
        -------
        InspectionResult dataclass with full analysis
        """
        previous_risk = machine.risk_level or "Low"

        # 1. Evaluate all rules
        builtin_triggered = self._evaluate_builtin_rules(machine)
        db_triggered      = self._evaluate_db_rules(machine, db_rules or [])

        # Deduplicate: DB rules may overlap with built-in ones
        all_triggered = builtin_triggered + db_triggered

        # 2. Determine final risk level (worst severity wins)
        risk_level = self._aggregate_risk(all_triggered)

        # 3. Calculate priority score
        overdue_days   = self._overdue_days(machine)
        priority_score = self._calculate_priority_score(machine, risk_level, all_triggered)

        # 4. Recommended action
        recommended_action = RECOMMENDATIONS.get(risk_level, "Continue Monitoring")

        # 5. Build explanation
        explanation = self._build_explanation(
            machine, risk_level, all_triggered, overdue_days
        )

        return InspectionResult(
            machine_id=machine.id,
            machine_code=machine.machine_code,
            machine_name=machine.name,
            machine_type=machine.machine_type,
            factory_section=machine.factory_section,
            status=machine.status,
            temperature=machine.temperature or 0.0,
            vibration=machine.vibration     or 0.0,
            pressure=machine.pressure       or 0.0,
            runtime_hours=machine.runtime_hours or 0.0,
            triggered_rules=all_triggered,
            risk_level=risk_level,
            previous_risk_level=previous_risk,
            priority_score=priority_score,
            recommended_action=recommended_action,
            explanation=explanation,
        )


# ── Singleton ─────────────────────────────────────────────────────────────────
inspection_engine = MachineInspectionEngine()
