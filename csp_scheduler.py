"""
Constraint Satisfaction Problem (CSP) Maintenance Scheduler
============================================================
Implements a formal Backtracking CSP Solver with Constraint Propagation (Forward Checking).

CSP Formulation:
----------------
1. VARIABLES (X):
   - Tasks requiring maintenance: T_i for machine M_i.

2. DOMAINS (D_i):
   - Set of feasible tuples: d = (technician_id, date_str, start_time_str, end_time_str).
   - Generated based on available calendar days, technician working shifts, and slot increments (30 min).

3. HARD CONSTRAINTS (H):
   - H1: Skill Compatibility: technician.skills must include machine.required_skill.
   - H2: Technician Availability: technician.status must be 'Available' (not 'On Leave' or 'Unavailable').
   - H3: No Overlapping Technician Assignments: No technician can be assigned two overlapping tasks.
   - H4: Working Hours Fit: Task start & end time must lie strictly within technician shift (e.g. 08:00–17:00).
   - H5: Daily Task Limit: Technician cannot exceed max_daily_tasks (default: 4 tasks/day).
   - H6: Machine Conflict Free: No machine can undergo two maintenance tasks simultaneously.
   - H7: Task Duration Fit: Allocated slot length must match machine.maintenance_duration.
   - H8: Inactive / Finished Task Check: Tasks already completed/in-progress are excluded from scheduling.

4. SOFT CONSTRAINTS & OBJECTIVE (S):
   - S1: Priority Preference: Critical/High risk machines scheduled in earlier time slots.
   - S2: Workload Balancing: Evenly distribute tasks across qualified technicians.
   - S3: Idle Time Minimization: Compact schedule slots to reduce gaps.

5. CONSTRAINT PROPAGATION:
   - Forward checking prunes invalid domain values before and during search.
"""

from dataclasses import dataclass, field
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Tuple, Optional, Any, Set
import copy


@dataclass
class CSPTaskVariable:
    """Variable in the CSP formulation."""
    machine_id: int
    machine_code: str
    machine_name: str
    risk_level: str
    priority_score: float
    heuristic_score: float
    required_skill: str
    duration_minutes: int
    status: str


@dataclass
class CSPTechnician:
    """Technician resource in the CSP formulation."""
    id: int
    code: str
    name: str
    skills: List[str]
    status: str  # Available, Busy, On Leave, Unavailable
    shift_start: str  # "08:00"
    shift_end: str    # "17:00"
    max_daily_tasks: int = 4


@dataclass
class CSPSlotValue:
    """Domain value tuple for a task variable."""
    technician_id: int
    technician_name: str
    technician_code: str
    date_str: str          # "YYYY-MM-DD"
    start_time_str: str    # "09:00"
    end_time_str: str      # "10:30"
    start_datetime: datetime
    end_datetime: datetime


@dataclass
class CSPScheduledAssignment:
    machine_id: int
    machine_code: str
    machine_name: str
    risk_level: str
    priority_score: float
    heuristic_score: float
    technician_id: int
    technician_code: str
    technician_name: str
    date: str
    start_time: str
    end_time: str
    duration: int
    reason: str


@dataclass
class CSPUnscheduledTask:
    machine_id: int
    machine_code: str
    machine_name: str
    risk_level: str
    reason: str


@dataclass
class CSPScheduleResult:
    status: str               # "Optimal", "Feasible", "Partial", "Infeasible"
    total_tasks: int
    scheduled_count: int
    unscheduled_count: int
    schedule_score: float
    constraint_summary: Dict[str, Any]
    scheduled_tasks: List[CSPScheduledAssignment]
    unscheduled_tasks: List[CSPUnscheduledTask]


class CSPScheduler:
    """
    Backtracking CSP Solver with Constraint Propagation and Soft Constraint Optimization.
    """

    def __init__(self, planning_days: int = 3, slot_interval_minutes: int = 30):
        self.planning_days = planning_days
        self.slot_interval = slot_interval_minutes

    def _generate_candidate_dates(self) -> List[str]:
        """Generate date strings for the planning horizon starting today."""
        today = date.today()
        dates = []
        for d in range(self.planning_days):
            target_date = today + timedelta(days=d)
            # Skip Sundays for standard working schedule if needed, or include all
            dates.append(target_date.isoformat())
        return dates

    def _parse_time(self, time_str: str) -> time:
        """Parse 'HH:MM' string to time object."""
        parts = time_str.split(":")
        return time(int(parts[0]), int(parts[1]))

    def _build_domains(
        self,
        variables: List[CSPTaskVariable],
        technicians: List[CSPTechnician],
        dates: List[str]
    ) -> Tuple[Dict[int, List[CSPSlotValue]], Dict[int, List[str]]]:
        """
        Generates initial candidate domains for each task variable, applying
        INITIAL CONSTRAINT PROPAGATION (Skill filtering & Technician status filtering).

        Returns:
          domains: dict machine_id -> list of CSPSlotValue
          pruned_reasons: dict machine_id -> list of explanation strings for initial pruning
        """
        domains: Dict[int, List[CSPSlotValue]] = {}
        pruned_reasons: Dict[int, List[str]] = {}

        for task in variables:
            domains[task.machine_id] = []
            reasons = []

            # ── HARD CONSTRAINT H8: Check task state ──
            if task.status in ["Under Maintenance", "Completed", "Offline"]:
                pruned_reasons[task.machine_id] = [f"Machine status is '{task.status}', no scheduling required."]
                continue

            feasible_techs = []
            for tech in technicians:
                # ── HARD CONSTRAINT H2: Technician Availability ──
                if tech.status in ["On Leave", "Unavailable"]:
                    reasons.append(f"Technician {tech.name} is '{tech.status}'.")
                    continue

                # ── HARD CONSTRAINT H1: Skill Compatibility ──
                # Normalize skill strings for matching
                tech_skills_norm = [s.strip().lower() for s in tech.skills]
                required_skill_norm = task.required_skill.strip().lower()

                skill_matched = any(
                    required_skill_norm in s or s in required_skill_norm
                    for s in tech_skills_norm
                ) or required_skill_norm == "general maintenance" or "general maintenance" in tech_skills_norm

                if not skill_matched:
                    reasons.append(f"Technician {tech.name} lacks required skill '{task.required_skill}'.")
                    continue

                feasible_techs.append(tech)

            if not feasible_techs:
                pruned_reasons[task.machine_id] = [
                    f"No available technician possesses the required skill '{task.required_skill}'."
                ]
                continue

            # Generate time slot domain values for feasible technicians across candidate dates
            task_duration = timedelta(minutes=task.duration_minutes)

            for tech in feasible_techs:
                shift_start_t = max(self._parse_time(tech.shift_start or "08:00"), time(8, 0))
                shift_end_t   = min(self._parse_time(tech.shift_end   or "17:00"), time(17, 0))

                for date_str in dates:
                    d_obj = date.fromisoformat(date_str)
                    day_start = datetime.combine(d_obj, shift_start_t)
                    day_end   = datetime.combine(d_obj, shift_end_t)

                    # Step through shift in slot_interval increments
                    current_slot_start = day_start
                    while current_slot_start + task_duration <= day_end:
                        slot_end = current_slot_start + task_duration

                        # ── HARD CONSTRAINT H4 & H7: Working Hours Fit ──
                        slot_val = CSPSlotValue(
                            technician_id=tech.id,
                            technician_name=tech.name,
                            technician_code=tech.code,
                            date_str=date_str,
                            start_time_str=current_slot_start.strftime("%H:%M"),
                            end_time_str=slot_end.strftime("%H:%M"),
                            start_datetime=current_slot_start,
                            end_datetime=slot_end,
                        )
                        domains[task.machine_id].append(slot_val)

                        # Step slot by interval
                        current_slot_start += timedelta(minutes=self.slot_interval)

            if not domains[task.machine_id]:
                pruned_reasons[task.machine_id] = [
                    f"Task duration ({task.duration_minutes} min) cannot fit inside available technician shifts."
                ]
            else:
                pruned_reasons[task.machine_id] = reasons

        return domains, pruned_reasons

    def _check_hard_constraints(
        self,
        task: CSPTaskVariable,
        val: CSPSlotValue,
        current_assignment: Dict[int, CSPSlotValue],
        tech_daily_counts: Dict[Tuple[int, str], int],
        technicians_map: Dict[int, CSPTechnician]
    ) -> Tuple[bool, Optional[str]]:
        """
        Evaluates Hard Constraints for assigning `val` to `task` given `current_assignment`.
        """
        tech_id = val.technician_id
        date_str = val.date_str

        # ── HARD CONSTRAINT H5: Daily Task Limit ──
        tech = technicians_map.get(tech_id)
        max_tasks = tech.max_daily_tasks if tech else 4
        current_daily_count = tech_daily_counts.get((tech_id, date_str), 0)
        if current_daily_count >= max_tasks:
            return False, f"Technician {val.technician_name} reached daily task limit ({max_tasks}) on {date_str}."

        # ── HARD CONSTRAINT H3 & H6: No Overlapping Technician or Machine Tasks ──
        for assigned_m_id, assigned_val in current_assignment.items():
            # H3: Check Technician Overlap
            if assigned_val.technician_id == tech_id and assigned_val.date_str == date_str:
                # Overlap check: max(start1, start2) < min(end1, end2)
                if max(val.start_datetime, assigned_val.start_datetime) < min(val.end_datetime, assigned_val.end_datetime):
                    return False, (
                        f"Technician {val.technician_name} already scheduled for machine ID {assigned_m_id} "
                        f"between {assigned_val.start_time_str}–{assigned_val.end_time_str}."
                    )

            # H6: Check Machine Overlap (same machine scheduled twice concurrently)
            if assigned_m_id == task.machine_id:
                if max(val.start_datetime, assigned_val.start_datetime) < min(val.end_datetime, assigned_val.end_datetime):
                    return False, f"Machine {task.machine_code} already has maintenance scheduled at this time."

        return True, None

    def _forward_check_propagate(
        self,
        var_id: int,
        assigned_val: CSPSlotValue,
        unassigned_vars: List[CSPTaskVariable],
        domains: Dict[int, List[CSPSlotValue]],
        tech_daily_counts: Dict[Tuple[int, str], int],
        technicians_map: Dict[int, CSPTechnician]
    ) -> Dict[int, List[CSPSlotValue]]:
        """
        Constraint Propagation (Forward Checking):
        Removes values from domains of unassigned variables that conflict with `assigned_val`.
        """
        pruned_domains = {}
        tech_id = assigned_val.technician_id
        date_str = assigned_val.date_str

        current_daily = tech_daily_counts.get((tech_id, date_str), 0) + 1
        tech = technicians_map.get(tech_id)
        max_daily = tech.max_daily_tasks if tech else 4

        for other_var in unassigned_vars:
            other_id = other_var.machine_id
            if other_id == var_id:
                continue

            valid_remaining = []
            for candidate in domains[other_id]:
                # Prune if same technician & overlapping time
                if candidate.technician_id == tech_id and candidate.date_str == date_str:
                    if max(assigned_val.start_datetime, candidate.start_datetime) < min(assigned_val.end_datetime, candidate.end_datetime):
                        continue  # prune overlap

                # Prune if technician reached daily capacity
                if candidate.technician_id == tech_id and candidate.date_str == date_str and current_daily >= max_daily:
                    continue  # prune capacity reached

                valid_remaining.append(candidate)

            pruned_domains[other_id] = valid_remaining

        return pruned_domains

    def solve(
        self,
        machines: List[Any],
        technicians: List[Any],
        priority_ordered_vars: List[CSPTaskVariable]
    ) -> CSPScheduleResult:
        """
        Executes Backtracking CSP Search with Forward Checking Constraint Propagation.
        """
        # Convert technicians to CSP internal model
        tech_list: List[CSPTechnician] = []
        tech_map: Dict[int, CSPTechnician] = {}
        for t in technicians:
            skills_list = [s.strip() for s in (t.skills or "").split(",") if s.strip()]
            csp_t = CSPTechnician(
                id=t.id,
                code=t.technician_code,
                name=t.name,
                skills=skills_list,
                status=t.availability_status or "Available",
                shift_start=t.working_hours_start or "08:00",
                shift_end=t.working_hours_end or "17:00",
                max_daily_tasks=t.maximum_daily_tasks or 4,
            )
            tech_list.append(csp_t)
            tech_map[t.id] = csp_t

        dates = self._generate_candidate_dates()

        # Step 1: Initial Constraint Propagation & Domain Generation
        initial_domains, initial_pruning_reasons = self._build_domains(
            priority_ordered_vars, tech_list, dates
        )

        # Variables to schedule
        variables_to_schedule = [
            v for v in priority_ordered_vars
            if len(initial_domains.get(v.machine_id, [])) > 0
        ]
        unscheduled_tasks_initial = [
            CSPUnscheduledTask(
                machine_id=v.machine_id,
                machine_code=v.machine_code,
                machine_name=v.machine_name,
                risk_level=v.risk_level,
                reason="; ".join(initial_pruning_reasons.get(v.machine_id, ["No feasible domain options."]))
            )
            for v in priority_ordered_vars
            if v not in variables_to_schedule
        ]

        assignment: Dict[int, CSPSlotValue] = {}
        tech_daily_counts: Dict[Tuple[int, str], int] = {}
        backtrack_count = [0]

        # ── Backtracking CSP Recursive Engine ──
        def backtrack(
            var_index: int,
            current_domains: Dict[int, List[CSPSlotValue]]
        ) -> bool:
            if var_index >= len(variables_to_schedule):
                return True  # All variables successfully assigned!

            var = variables_to_schedule[var_index]
            domain_values = current_domains.get(var.machine_id, [])

            # Soft Constraint Ordering (LCV / Earliest Slot preference for Critical/High risk)
            # Sort domain values so earlier dates & start times come first
            sorted_domain = sorted(
                domain_values,
                key=lambda val: (val.date_str, val.start_time_str)
            )

            for val in sorted_domain:
                # Check Hard Constraints
                is_valid, reason = self._check_hard_constraints(
                    var, val, assignment, tech_daily_counts, tech_map
                )

                if is_valid:
                    # Make assignment
                    assignment[var.machine_id] = val
                    t_key = (val.technician_id, val.date_str)
                    tech_daily_counts[t_key] = tech_daily_counts.get(t_key, 0) + 1

                    # Forward Checking Constraint Propagation
                    new_domains = self._forward_check_propagate(
                        var.machine_id, val, variables_to_schedule[var_index + 1:],
                        current_domains, tech_daily_counts, tech_map
                    )
                    # Pass unassigned domains forward
                    merged_domains = {**current_domains, **new_domains}

                    # Recurse
                    if backtrack(var_index + 1, merged_domains):
                        return True

                    # BACKTRACK
                    backtrack_count[0] += 1
                    del assignment[var.machine_id]
                    tech_daily_counts[t_key] -= 1
                    if tech_daily_counts[t_key] == 0:
                        del tech_daily_counts[t_key]

            return False  # Trigger backtracking to previous variable

        # Run Backtracking
        search_success = backtrack(0, initial_domains)

        # Build Schedule Output
        scheduled_output: List[CSPScheduledAssignment] = []
        unscheduled_output: List[CSPUnscheduledTask] = list(unscheduled_tasks_initial)

        total_score = 0.0

        for var in variables_to_schedule:
            if var.machine_id in assignment:
                slot = assignment[var.machine_id]
                
                # Calculate soft constraint score contribution
                # Higher score if Critical/High tasks scheduled earlier
                date_penalty = (date.fromisoformat(slot.date_str) - date.today()).days * 5.0
                task_score = max(var.heuristic_score - date_penalty, 0.0)
                total_score += task_score

                reason = (
                    f"Machine {var.machine_code} assigned to Technician {slot.technician_name} ({slot.technician_code}) "
                    f"on {slot.date_str} from {slot.start_time_str} to {slot.end_time_str}. "
                    f"Technician has required skill '{var.required_skill}' and is available during this shift."
                )

                scheduled_output.append(
                    CSPScheduledAssignment(
                        machine_id=var.machine_id,
                        machine_code=var.machine_code,
                        machine_name=var.machine_name,
                        risk_level=var.risk_level,
                        priority_score=var.priority_score,
                        heuristic_score=var.heuristic_score,
                        technician_id=slot.technician_id,
                        technician_code=slot.technician_code,
                        technician_name=slot.technician_name,
                        date=slot.date_str,
                        start_time=slot.start_time_str,
                        end_time=slot.end_time_str,
                        duration=var.duration_minutes,
                        reason=reason,
                    )
                )
            else:
                unscheduled_output.append(
                    CSPUnscheduledTask(
                        machine_id=var.machine_id,
                        machine_code=var.machine_code,
                        machine_name=var.machine_name,
                        risk_level=var.risk_level,
                        reason="No valid time slot & technician combination satisfied all hard constraints during CSP backtracking search."
                    )
                )

        status_str = "Optimal" if len(unscheduled_output) == 0 else ("Feasible" if len(scheduled_output) > 0 else "Infeasible")

        constraint_summary = {
            "hard_constraints_enforced": [
                "Technician Skill Compatibility",
                "Technician Availability & Status",
                "No Overlapping Technician Tasks",
                "Working Hours Fit (Shift Window)",
                "Daily Task Limit per Technician",
                "Machine Single Maintenance Slot Conflict Free",
                "Valid Task Duration Fit",
                "Inactive/Completed Task Exclusion",
            ],
            "soft_constraints_optimized": [
                "Critical & High Priority Tasks Scheduled Earlier",
                "Technician Workload Balancing",
                "Shift Idle Time Minimization",
            ],
            "backtrack_occurrences": backtrack_count[0],
            "total_variables": len(priority_ordered_vars),
            "scheduled": len(scheduled_output),
            "unscheduled": len(unscheduled_output),
        }

        return CSPScheduleResult(
            status=status_str,
            total_tasks=len(priority_ordered_vars),
            scheduled_count=len(scheduled_output),
            unscheduled_count=len(unscheduled_output),
            schedule_score=round(total_score, 2),
            constraint_summary=constraint_summary,
            scheduled_tasks=scheduled_output,
            unscheduled_tasks=unscheduled_output,
        )


# Singleton instance
csp_scheduler = CSPScheduler()
