"""
AI Problem Formulation & Heuristic Priority Module
===================================================
Formal AI Problem Definition for Factory Maintenance Prioritization.

AI Problem Formulation:
-----------------------
1. INITIAL STATE (S_0):
   - Set of machines M = {m_1, m_2, ..., m_n} with sensor readings, risk levels, 
     priority scores, overdue days, required technician skills, and maintenance durations.
   - Available maintenance resources and technicians.

2. STATE REPRESENTATION:
   - State S = tuple of machine maintenance statuses, current queue order, and remaining unhandled machines.
   - Machine State s_i = (id, code, risk_level, priority_score, status, maintenance_duration, required_skill, overdue_days)

3. AVAILABLE ACTIONS (A):
   - Action SelectMachine(m_i): Select unassigned machine m_i from the pool to be scheduled next for maintenance/inspection.

4. GOAL STATE (G):
   - All high-risk and critical machines are ordered into a prioritized queue according to heuristic urgency score h(s),
     ensuring maximum factory risk reduction per maintenance turn.

5. HEURISTIC FUNCTION h(s):
   - Urgency estimator mapping state s_i -> Float score [0.0 to 200.0+].
   - Higher h(s) = Greater urgency to perform maintenance.
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import heapq


@dataclass
class MachineState:
    """State representation of an individual machine in the formulation problem."""
    id: int
    machine_code: str
    name: str
    machine_type: str
    factory_section: str
    status: str
    risk_level: str
    priority_score: float
    required_skill: str
    maintenance_duration: int  # in minutes
    last_maintenance_date: Optional[datetime] = None
    next_maintenance_date: Optional[datetime] = None
    overdue_days: int = 0


@dataclass
class PrioritizedMachine:
    """Result tuple produced by the Problem-Solving Agent priority queue."""
    rank: int
    machine_id: int
    machine_code: str
    machine_name: str
    risk_level: str
    priority_score: float
    heuristic_score: float
    maintenance_duration: int
    required_skill: str
    reason: str


class MaintenanceProblemFormulation:
    """
    Formal AI Problem Formulation & Heuristic Priority Evaluation Agent.
    """

    # Weight parameters for heuristic function h(s)
    RISK_WEIGHTS = {
        "Critical": 50.0,
        "High": 35.0,
        "Medium": 15.0,
        "Low": 0.0,
    }

    STATUS_BONUS = {
        "Critical": 20.0,
        "Warning": 10.0,
        "Operational": 0.0,
        "Under Maintenance": -50.0,  # lower urgency if already being maintained
        "Offline": -10.0,
    }

    def compute_overdue_days(self, machine) -> int:
        """Calculate number of days maintenance is overdue."""
        if not machine.next_maintenance_date:
            return 0
        
        now = datetime.now()
        target = machine.next_maintenance_date
        if isinstance(target, str):
            try:
                target = datetime.fromisoformat(target)
            except ValueError:
                return 0
        
        if now > target:
            return max((now - target).days, 0)
        return 0

    def calculate_heuristic(self, state: MachineState) -> tuple[float, str]:
        """
        Heuristic Function h(s):
        Estimates the urgency of performing maintenance on machine state `s`.

        Formula:
          h(s) = Base_Risk_Score(risk_level)
               + 0.4 * Priority_Score
               + Status_Bonus(status)
               + min(Overdue_Days * 3.0, 30.0)
               + Short_Job_ROI_Bonus (prefer quick-wins for equal risk: max 10 - 0.05 * duration)

        Returns:
          (heuristic_score, explainable_reason)
        """
        # 1. Base Risk Score
        risk_term = self.RISK_WEIGHTS.get(state.risk_level, 0.0)

        # 2. Priority Score component (from inspection engine)
        priority_term = 0.4 * (state.priority_score or 0.0)

        # 3. Status Bonus
        status_term = self.STATUS_BONUS.get(state.status, 0.0)

        # 4. Overdue Penalty
        overdue_term = min(state.overdue_days * 3.0, 30.0)

        # 5. Duration ROI Efficiency (shorter maintenance jobs get slight bonus for throughput)
        duration_mins = state.maintenance_duration or 60
        duration_term = max(10.0 - (duration_mins / 30.0), 0.0)

        # Total Heuristic Score
        h_score = round(risk_term + priority_term + status_term + overdue_term + duration_term, 2)

        # Build Explainability Reason
        reasons = []
        if state.risk_level in ["Critical", "High"]:
            reasons.append(f"{state.risk_level} risk level (+{risk_term:.0f})")
        if state.priority_score > 50:
            reasons.append(f"high priority score {state.priority_score:.1f}")
        if state.overdue_days > 0:
            reasons.append(f"overdue by {state.overdue_days} day(s)")
        if state.status in ["Critical", "Warning"]:
            reasons.append(f"status '{state.status}'")
        if not reasons:
            reasons.append("routine operational monitoring")

        reason_text = f"Urgency h(s)={h_score}: Driven by " + ", ".join(reasons) + "."

        return h_score, reason_text

    def solve_prioritization(self, machines: List[Any]) -> List[PrioritizedMachine]:
        """
        Solves the maintenance prioritization problem using a Priority Queue.

        Returns list of PrioritizedMachine objects sorted by heuristic urgency h(s) descending.
        """
        # Priority queue using max-heap (storing negative heuristic score for max-heap in Python min-heap)
        heap = []

        for m in machines:
            overdue = self.compute_overdue_days(m)
            state = MachineState(
                id=m.id,
                machine_code=m.machine_code,
                name=m.name,
                machine_type=m.machine_type,
                factory_section=m.factory_section,
                status=m.status,
                risk_level=m.risk_level or "Low",
                priority_score=m.priority_score or 0.0,
                required_skill=m.required_skill or "General Maintenance",
                maintenance_duration=m.maintenance_duration or 60,
                last_maintenance_date=m.last_maintenance_date,
                next_maintenance_date=m.next_maintenance_date,
                overdue_days=overdue,
            )

            h_score, reason = self.calculate_heuristic(state)

            # Heap tuple: (-h_score, -priority_score, machine_id, state, reason)
            # Negative numbers used because heapq is a min-heap
            heapq.heappush(heap, (-h_score, -(state.priority_score or 0.0), m.id, state, reason))

        # Extract in order of highest heuristic score
        prioritized_list = []
        rank = 1
        while heap:
            neg_h, neg_p, m_id, state, reason = heapq.heappop(heap)
            h_score = -neg_h

            prioritized_list.append(
                PrioritizedMachine(
                    rank=rank,
                    machine_id=state.id,
                    machine_code=state.machine_code,
                    machine_name=state.name,
                    risk_level=state.risk_level,
                    priority_score=state.priority_score,
                    heuristic_score=h_score,
                    maintenance_duration=state.maintenance_duration,
                    required_skill=state.required_skill,
                    reason=reason,
                )
            )
            rank += 1

        return prioritized_list


# Singleton instance
problem_planner = MaintenanceProblemFormulation()
