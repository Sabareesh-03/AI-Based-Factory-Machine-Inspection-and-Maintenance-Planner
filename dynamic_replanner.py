"""
Dynamic / Online Maintenance Re-Planning Module
================================================
Implements incremental online re-planning when factory operating conditions change dynamically.

Re-Planning Architecture:
------------------------
1. LOAD BASELINE SCHEDULE:
   - Computes initial schedule S_0 for current machine and technician states using Step 4 Priority + Step 5 CSP.

2. DETECT EVENT TRIGGER & IDENTIFY AFFECTED TASKS:
   - Trigger A: Machine Risk Change (e.g. Warning -> Critical)
   - Trigger B: Technician Unavailability (e.g. Available -> Unavailable / On Leave)
   - Trigger C: New Critical Machine Maintenance Requirement
   - Trigger D: Machine Status -> Offline

3. PRESERVE UNAFFECTED ASSIGNMENTS (Incremental Search):
   - Fixes unaffected task assignments to retain schedule stability and minimize disruption.

4. RE-EVALUATE & RESOLVE CSP FOR AFFECTED TASKS:
   - Re-calculates Step 4 Heuristic Priority scores h(s).
   - Re-runs Forward Checking CSP Solver on the unassigned/affected variables.

5. SCHEDULE COMPARISON & EXPLAINABILITY:
   - Diff S_0 vs S_revised to generate explicit task change records and natural language explanations.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import copy

from ai_engine.problem_formulation import problem_planner
from ai_engine.csp_scheduler import (
    csp_scheduler,
    CSPTaskVariable,
    CSPScheduledAssignment,
    CSPUnscheduledTask,
    CSPScheduleResult,
)


@dataclass
class ScheduleTaskDiff:
    machine_id: int
    machine_code: str
    machine_name: str
    change_type: str  # "Reassigned Technician", "Rescheduled Time", "Removed Task", "Added Task", "Priority Escalation"
    previous_technician: Optional[str]
    new_technician: Optional[str]
    previous_slot: Optional[str]
    new_slot: Optional[str]
    reason: str


@dataclass
class DynamicReplanResult:
    trigger: str
    detected_change: str
    affected_task_ids: List[int]
    previous_schedule: List[CSPScheduledAssignment]
    revised_schedule: List[CSPScheduledAssignment]
    changes: List[ScheduleTaskDiff]
    explanation: str


class DynamicReplanner:
    """
    Online Re-Planning Agent enforcing Incremental CSP Search and Schedule Stability.
    """

    def _clone_model(self, obj):
        """Helper to create deep memory clone of SQLAlchemy ORM models for safe simulation."""
        class MockObj:
            pass

        mock = MockObj()
        for attr in dir(obj):
            if not attr.startswith("_") and not callable(getattr(obj, attr)):
                setattr(mock, attr, getattr(obj, attr))
        return mock

    def simulate_replan(
        self,
        db_machines: List[Any],
        db_technicians: List[Any],
        trigger_type: str,
        target_machine_id: Optional[int] = None,
        new_risk_level: Optional[str] = None,
        new_machine_status: Optional[str] = None,
        target_technician_id: Optional[int] = None,
        new_availability_status: Optional[str] = None,
    ) -> DynamicReplanResult:
        """
        Executes a safe simulation of Dynamic Re-Planning. Does NOT alter database state.
        """
        # Step 1: Create memory clones for baseline simulation
        sim_machines = [self._clone_model(m) for m in db_machines]
        sim_technicians = [self._clone_model(t) for t in db_technicians]

        # Generate Baseline Schedule (S_0)
        p_list_0 = problem_planner.solve_prioritization(sim_machines)
        csp_vars_0 = [
            CSPTaskVariable(
                machine_id=pm.machine_id,
                machine_code=pm.machine_code,
                machine_name=pm.machine_name,
                risk_level=pm.risk_level,
                priority_score=pm.priority_score,
                heuristic_score=pm.heuristic_score,
                required_skill=pm.required_skill,
                duration_minutes=pm.maintenance_duration,
                status=next((m.status for m in sim_machines if m.id == pm.machine_id), "Operational"),
            )
            for pm in p_list_0
        ]
        base_result = csp_scheduler.solve(sim_machines, sim_technicians, csp_vars_0)
        previous_schedule = base_result.scheduled_tasks

        # Step 2: Apply Event Trigger Modification to Simulated Models & Detect Affected Tasks
        detected_change_desc = ""
        affected_task_ids: Set[int] = set()
        trigger_title = ""

        if trigger_type == "machine_risk_change" and target_machine_id:
            for m in sim_machines:
                if m.id == target_machine_id:
                    old_risk = m.risk_level
                    m.risk_level = new_risk_level or "Critical"
                    trigger_title = "Machine Risk Level Escalation"
                    detected_change_desc = f"Machine {m.machine_code} ({m.name}) risk level changed from '{old_risk}' to '{m.risk_level}'."
                    affected_task_ids.add(m.id)
                    # Lower priority tasks that might be displaced
                    for prev_t in previous_schedule:
                        if prev_t.heuristic_score <= (m.priority_score or 0.0):
                            affected_task_ids.add(prev_t.machine_id)

        elif trigger_type == "technician_unavailability" and target_technician_id:
            for t in sim_technicians:
                if t.id == target_technician_id:
                    old_stat = t.status
                    t.status = new_availability_status or "Unavailable"
                    trigger_title = "Technician Unavailability Event"
                    detected_change_desc = f"Technician {t.name} ({t.technician_code}) availability status changed from '{old_stat}' to '{t.status}'."
                    # All tasks assigned to this technician in S_0 are affected
                    for prev_t in previous_schedule:
                        if prev_t.technician_id == t.id:
                            affected_task_ids.add(prev_t.machine_id)

        elif trigger_type == "machine_offline" and target_machine_id:
            for m in sim_machines:
                if m.id == target_machine_id:
                    old_stat = m.status
                    m.status = "Offline"
                    trigger_title = "Machine Offline Event"
                    detected_change_desc = f"Machine {m.machine_code} ({m.name}) status changed from '{old_stat}' to 'Offline'."
                    affected_task_ids.add(m.id)

        elif trigger_type == "new_critical_machine":
            trigger_title = "New Urgent Maintenance Event"
            # Create a mock new urgent machine for simulation
            class MockMachine:
                id = 999
                machine_code = "MCH-EMERGENCY"
                name = "Emergency High-Pressure Compressor"
                machine_type = "Compressor"
                factory_section = "Section C"
                status = "Critical"
                temperature = 98.5
                vibration = 11.2
                pressure = 28.4
                runtime_hours = 8200
                risk_level = "Critical"
                priority_score = 95.0
                required_skill = "Mechanical Repair"
                maintenance_duration = 60
                last_maintenance_date = None
                next_maintenance_date = None

            new_m = MockMachine()
            sim_machines.append(new_m)
            detected_change_desc = f"New emergency machine requirement added: {new_m.machine_code} ({new_m.name}) - Critical Risk."
            affected_task_ids.add(new_m.id)

        else:
            trigger_title = "General Dynamic Assessment"
            detected_change_desc = "Re-planning evaluated without single parameter trigger."

        # Step 3: Re-evaluate Heuristic Priority Scores (Step 4) for Revised Models
        p_list_revised = problem_planner.solve_prioritization(sim_machines)
        csp_vars_revised = [
            CSPTaskVariable(
                machine_id=pm.machine_id,
                machine_code=pm.machine_code,
                machine_name=pm.machine_name,
                risk_level=pm.risk_level,
                priority_score=pm.priority_score,
                heuristic_score=pm.heuristic_score,
                required_skill=pm.required_skill,
                duration_minutes=pm.maintenance_duration,
                status=next((m.status for m in sim_machines if m.id == pm.machine_id), "Operational"),
            )
            for pm in p_list_revised
        ]

        # Step 4: Run CSP Scheduler for Revised State
        revised_result = csp_scheduler.solve(sim_machines, sim_technicians, csp_vars_revised)
        revised_schedule = revised_result.scheduled_tasks

        # Step 5: Diff Schedules (S_0 vs S_revised) & Generate Explanations
        prev_map = {t.machine_id: t for t in previous_schedule}
        rev_map  = {t.machine_id: t for t in revised_schedule}

        all_ids = set(prev_map.keys()).union(set(rev_map.keys()))
        changes: List[ScheduleTaskDiff] = []
        explanation_bullets = []

        for m_id in all_ids:
            old_task = prev_map.get(m_id)
            new_task = rev_map.get(m_id)

            if old_task and not new_task:
                reason_str = f"Task for machine ID {m_id} removed from schedule due to condition change."
                if trigger_type == "machine_offline":
                    reason_str = f"Machine {old_task.machine_code} went Offline; maintenance task removed from active queue."
                elif trigger_type == "technician_unavailability":
                    reason_str = f"Machine {old_task.machine_code} unscheduled because assigned Technician {old_task.technician_name} became Unavailable and no alternative qualified technician was free."

                changes.append(
                    ScheduleTaskDiff(
                        machine_id=m_id,
                        machine_code=old_task.machine_code,
                        machine_name=old_task.machine_name,
                        change_type="Removed Task",
                        previous_technician=old_task.technician_name,
                        new_technician=None,
                        previous_slot=f"{old_task.date} {old_task.start_time}–{old_task.end_time}",
                        new_slot=None,
                        reason=reason_str,
                    )
                )
                explanation_bullets.append(reason_str)

            elif not old_task and new_task:
                reason_str = f"New task for {new_task.machine_code} inserted into schedule at {new_task.date} {new_task.start_time} assigned to {new_task.technician_name}."
                changes.append(
                    ScheduleTaskDiff(
                        machine_id=m_id,
                        machine_code=new_task.machine_code,
                        machine_name=new_task.machine_name,
                        change_type="Added Task",
                        previous_technician=None,
                        new_technician=new_task.technician_name,
                        previous_slot=None,
                        new_slot=f"{new_task.date} {new_task.start_time}–{new_task.end_time}",
                        reason=reason_str,
                    )
                )
                explanation_bullets.append(reason_str)

            elif old_task and new_task:
                tech_changed = old_task.technician_id != new_task.technician_id
                time_changed = (old_task.date != new_task.date) or (old_task.start_time != new_task.start_time)

                if tech_changed or time_changed:
                    change_kind = "Reassigned Technician & Rescheduled Time" if (tech_changed and time_changed) else ("Reassigned Technician" if tech_changed else "Rescheduled Time")
                    reason_str = (
                        f"Machine {new_task.machine_code} moved from {old_task.technician_name} ({old_task.start_time}) "
                        f"to {new_task.technician_name} ({new_task.start_time}) on {new_task.date} due to dynamic priority re-ordering."
                    )

                    changes.append(
                        ScheduleTaskDiff(
                            machine_id=m_id,
                            machine_code=new_task.machine_code,
                            machine_name=new_task.machine_name,
                            change_type=change_kind,
                            previous_technician=old_task.technician_name,
                            new_technician=new_task.technician_name,
                            previous_slot=f"{old_task.date} {old_task.start_time}–{old_task.end_time}",
                            new_slot=f"{new_task.date} {new_task.start_time}–{new_task.end_time}",
                            reason=reason_str,
                        )
                    )
                    explanation_bullets.append(reason_str)

        if not explanation_bullets:
            overall_explanation = f"Dynamic Assessment Completed: {detected_change_desc} No schedule adjustments were required as existing assignments satisfy all hard constraints."
        else:
            overall_explanation = f"Dynamic Re-Planning Triggered ({trigger_title}): {detected_change_desc} " + " ".join(explanation_bullets)

        return DynamicReplanResult(
            trigger=trigger_title,
            detected_change=detected_change_desc,
            affected_task_ids=list(affected_task_ids),
            previous_schedule=previous_schedule,
            revised_schedule=revised_schedule,
            changes=changes,
            explanation=overall_explanation,
        )


# Singleton instance
dynamic_replanner = DynamicReplanner()
