"""
AI Maintenance Planner Orchestration Service (Backend Only)
============================================================
Coordinates existing AI sub-engines into a single unified planning workflow:
  1. Read current machine data & evaluate rules/inspection (Step 3 & 7)
  2. Compute heuristic priority queue h(s) (Step 4)
  3. Execute CSP Backtracking search with Forward Checking (Step 5)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from ai_engine.inspection_engine import inspection_engine
from ai_engine.problem_formulation import problem_planner
from ai_engine.csp_scheduler import (
    csp_scheduler,
    CSPTaskVariable,
    CSPScheduledAssignment,
    CSPUnscheduledTask,
    CSPScheduleResult,
)


@dataclass
class FullPlanRunResult:
    status: str
    timestamp: str
    total_machines: int
    machines_requiring_attention: int
    critical_count: int
    high_risk_count: int
    scheduled_task_count: int
    unscheduled_task_count: int
    prioritized_machines: List[Any]
    generated_schedule: List[CSPScheduledAssignment]
    unscheduled_tasks: List[CSPUnscheduledTask]
    schedule_score: float
    explanation: str


class AIMaintenancePlannerOrchestrator:
    """
    Backend Orchestration Service coordinating Inspection Engine, Heuristic Planner,
    and CSP Solver.
    """

    def run_full_planning(
        self,
        db_machines: List[Any],
        db_rules: List[Any],
        db_technicians: List[Any]
    ) -> FullPlanRunResult:
        """
        Executes end-to-end AI planning pipeline over current database state.
        Safe execution — does NOT mutate database records or create duplicates.
        """
        if not db_machines:
            return FullPlanRunResult(
                status="No Data",
                timestamp=datetime.now().isoformat(),
                total_machines=0,
                machines_requiring_attention=0,
                critical_count=0,
                high_risk_count=0,
                scheduled_task_count=0,
                unscheduled_task_count=0,
                prioritized_machines=[],
                generated_schedule=[],
                unscheduled_tasks=[],
                schedule_score=0.0,
                explanation="No machines found in database to evaluate.",
            )

        # Step 1: Run Inspection & Rule Engine across all machines
        inspected_results = []
        crit_c = high_c = med_c = 0

        for machine in db_machines:
            res = inspection_engine.inspect(machine, db_rules=db_rules)
            inspected_results.append(res)
            # Assign in-memory attributes for downstream evaluation
            machine.risk_level = res.risk_level
            machine.priority_score = res.priority_score

            if res.risk_level == "Critical": crit_c += 1
            elif res.risk_level == "High": high_c += 1
            elif res.risk_level == "Medium": med_c += 1

        attention_count = crit_c + high_c + med_c

        # Step 2: Obtain Priority Ordering using Heuristic Planner (Step 4)
        prioritized_queue = problem_planner.solve_prioritization(db_machines)

        # Step 3: Build CSP Variables in Priority Queue Order (Step 5)
        csp_vars = [
            CSPTaskVariable(
                machine_id=pm.machine_id,
                machine_code=pm.machine_code,
                machine_name=pm.machine_name,
                risk_level=pm.risk_level,
                priority_score=pm.priority_score,
                heuristic_score=pm.heuristic_score,
                required_skill=pm.required_skill,
                duration_minutes=pm.maintenance_duration,
                status=next((m.status for m in db_machines if m.id == pm.machine_id), "Operational"),
            )
            for pm in prioritized_queue
        ]

        # Step 4: Run CSP Scheduler (Step 5)
        if not db_technicians:
            explanation_msg = f"Evaluated {len(db_machines)} machines. Identified {attention_count} requiring attention ({crit_c} Critical, {high_c} High risk). No available technicians found to schedule tasks."
            return FullPlanRunResult(
                status="No Technicians",
                timestamp=datetime.now().isoformat(),
                total_machines=len(db_machines),
                machines_requiring_attention=attention_count,
                critical_count=crit_c,
                high_risk_count=high_c,
                scheduled_task_count=0,
                unscheduled_task_count=len(prioritized_queue),
                prioritized_machines=prioritized_queue,
                generated_schedule=[],
                unscheduled_tasks=[
                    CSPUnscheduledTask(
                        machine_id=pm.machine_id,
                        machine_code=pm.machine_code,
                        machine_name=pm.machine_name,
                        risk_level=pm.risk_level,
                        reason="No technicians available in database."
                    ) for pm in prioritized_queue
                ],
                schedule_score=0.0,
                explanation=explanation_msg,
            )

        csp_res: CSPScheduleResult = csp_scheduler.solve(db_machines, db_technicians, csp_vars)

        explanation_msg = (
            f"Full AI Maintenance Plan generated successfully. Inspected {len(db_machines)} machines "
            f"({crit_c} Critical, {high_c} High risk). Ordered candidates via Heuristic Priority Queue h(s). "
            f"CSP Backtracking search scheduled {csp_res.scheduled_count} tasks ({csp_res.unscheduled_count} unscheduled due to constraints)."
        )

        return FullPlanRunResult(
            status="success",
            timestamp=datetime.now().isoformat(),
            total_machines=len(db_machines),
            machines_requiring_attention=attention_count,
            critical_count=crit_c,
            high_risk_count=high_c,
            scheduled_task_count=csp_res.scheduled_count,
            unscheduled_task_count=csp_res.unscheduled_count,
            prioritized_machines=prioritized_queue,
            generated_schedule=csp_res.scheduled_tasks,
            unscheduled_tasks=csp_res.unscheduled_tasks,
            schedule_score=csp_res.schedule_score,
            explanation=explanation_msg,
        )


# Singleton instance
maintenance_orchestrator = AIMaintenancePlannerOrchestrator()
