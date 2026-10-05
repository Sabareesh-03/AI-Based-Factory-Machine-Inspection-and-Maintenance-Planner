"""
Seed Script — Demo Data for Factory Maintenance Planner
-------------------------------------------------------
Creates:
  • 15 machines  (varied conditions: Normal / Warning / Critical)
  •  6 technicians
  •  8 maintenance history records
  •  5 alerts
  •  5 maintenance tasks
  •  5 rules

Run from the backend/ directory:
    python seed.py
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Initialize DB tables first
from database.init_db import init_db
init_db()

from database.db import SessionLocal
from app.models.machine import Machine, MachineStatus, RiskLevel
from app.models.technician import Technician, AvailabilityStatus, ExperienceLevel
from app.models.maintenance_task import MaintenanceTask, TaskStatus, TaskPriority
from app.models.maintenance_history import MaintenanceHistory
from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.models.rule import Rule, RuleSeverity

# ── Helpers ───────────────────────────────────────────────────────────────────
now   = datetime.utcnow
days  = lambda n: now() + timedelta(days=n)
hours = lambda n: now() + timedelta(hours=n)


def seed():
    db = SessionLocal()
    try:
        # ── Guard: skip if already seeded ─────────────────────────────────────
        if db.query(Machine).count() > 0:
            print("⚠️  Demo data already exists. Skipping seed. (Drop the DB to re-seed)")
            return

        print("\n🌱 Seeding demo data...\n")

        # ── 1. TECHNICIANS ─────────────────────────────────────────────────────
        technicians = [
            Technician(
                technician_code="TECH-001",
                name="John Smith",
                department="Mechanical Maintenance",
                skills="Mechanical,Hydraulics,Pneumatics",
                experience_level=ExperienceLevel.EXPERT,
                availability_status=AvailabilityStatus.AVAILABLE,
                working_hours_start="08:00", working_hours_end="17:00",
                maximum_daily_tasks=5, current_workload=2,
            ),
            Technician(
                technician_code="TECH-002",
                name="Maria Garcia",
                department="Electrical Maintenance",
                skills="Electrical,PLC,Automation",
                experience_level=ExperienceLevel.SENIOR,
                availability_status=AvailabilityStatus.AVAILABLE,
                working_hours_start="08:00", working_hours_end="17:00",
                maximum_daily_tasks=4, current_workload=1,
            ),
            Technician(
                technician_code="TECH-003",
                name="David Chen",
                department="Hydraulics & Pneumatics",
                skills="Hydraulics,Pneumatics,Mechanical",
                experience_level=ExperienceLevel.INTERMEDIATE,
                availability_status=AvailabilityStatus.BUSY,
                working_hours_start="07:00", working_hours_end="16:00",
                maximum_daily_tasks=4, current_workload=4,
            ),
            Technician(
                technician_code="TECH-004",
                name="Sarah Johnson",
                department="Electronics & Robotics",
                skills="Electronics,Robotics,Sensors,PLC",
                experience_level=ExperienceLevel.EXPERT,
                availability_status=AvailabilityStatus.AVAILABLE,
                working_hours_start="09:00", working_hours_end="18:00",
                maximum_daily_tasks=5, current_workload=0,
            ),
            Technician(
                technician_code="TECH-005",
                name="Michael Brown",
                department="General Maintenance",
                skills="Mechanical,Electrical,General",
                experience_level=ExperienceLevel.JUNIOR,
                availability_status=AvailabilityStatus.AVAILABLE,
                working_hours_start="08:00", working_hours_end="17:00",
                maximum_daily_tasks=3, current_workload=1,
            ),
            Technician(
                technician_code="TECH-006",
                name="Priya Patel",
                department="Instrumentation",
                skills="Instrumentation,Sensors,Electrical,Automation",
                experience_level=ExperienceLevel.SENIOR,
                availability_status=AvailabilityStatus.ON_LEAVE,
                working_hours_start="08:00", working_hours_end="17:00",
                maximum_daily_tasks=4, current_workload=0,
            ),
        ]
        db.add_all(technicians)
        db.flush()
        print(f"   ✅ {len(technicians)} technicians created")

        # ── 2. MACHINES ────────────────────────────────────────────────────────
        machines = [
            # ── Normal / Operational Machines ──────────────────────────────────
            Machine(
                machine_code="MCH-001", name="CNC Milling Machine #1",
                machine_type="CNC Machine", factory_section="Section A",
                status=MachineStatus.OPERATIONAL, risk_level=RiskLevel.LOW,
                temperature=42.5, vibration=1.2, pressure=5.0,
                runtime_hours=1240.0, priority_score=10.0,
                required_skill="Mechanical",
                maintenance_duration=90,
                last_maintenance_date=days(-30),
                next_maintenance_date=days(60),
            ),
            Machine(
                machine_code="MCH-002", name="Assembly Robot Arm #1",
                machine_type="Robotic System", factory_section="Section B",
                status=MachineStatus.OPERATIONAL, risk_level=RiskLevel.LOW,
                temperature=38.0, vibration=0.8, pressure=0.0,
                runtime_hours=820.0, priority_score=8.0,
                required_skill="Robotics",
                maintenance_duration=120,
                last_maintenance_date=days(-15),
                next_maintenance_date=days(75),
            ),
            Machine(
                machine_code="MCH-003", name="Conveyor Belt System #1",
                machine_type="Conveyor", factory_section="Section A",
                status=MachineStatus.OPERATIONAL, risk_level=RiskLevel.LOW,
                temperature=35.0, vibration=1.5, pressure=3.5,
                runtime_hours=3200.0, priority_score=12.0,
                required_skill="Mechanical",
                maintenance_duration=60,
                last_maintenance_date=days(-20),
                next_maintenance_date=days(40),
            ),
            Machine(
                machine_code="MCH-004", name="Welding Station #2",
                machine_type="Welding Equipment", factory_section="Section C",
                status=MachineStatus.OPERATIONAL, risk_level=RiskLevel.LOW,
                temperature=55.0, vibration=2.1, pressure=8.0,
                runtime_hours=950.0, priority_score=15.0,
                required_skill="Electrical",
                maintenance_duration=75,
                last_maintenance_date=days(-45),
                next_maintenance_date=days(45),
            ),
            Machine(
                machine_code="MCH-005", name="Air Compressor Unit #1",
                machine_type="Air Compressor", factory_section="Utility Room",
                status=MachineStatus.OPERATIONAL, risk_level=RiskLevel.LOW,
                temperature=48.0, vibration=3.0, pressure=12.0,
                runtime_hours=5100.0, priority_score=18.0,
                required_skill="Mechanical",
                maintenance_duration=45,
                last_maintenance_date=days(-10),
                next_maintenance_date=days(80),
            ),
            Machine(
                machine_code="MCH-006", name="Quality Control Scanner",
                machine_type="Inspection System", factory_section="Section D",
                status=MachineStatus.OPERATIONAL, risk_level=RiskLevel.LOW,
                temperature=30.0, vibration=0.5, pressure=0.0,
                runtime_hours=430.0, priority_score=5.0,
                required_skill="Electronics",
                maintenance_duration=60,
                last_maintenance_date=days(-60),
                next_maintenance_date=days(120),
            ),
            Machine(
                machine_code="MCH-007", name="Packaging Machine #1",
                machine_type="Packaging", factory_section="Section E",
                status=MachineStatus.OPERATIONAL, risk_level=RiskLevel.LOW,
                temperature=40.0, vibration=2.5, pressure=4.0,
                runtime_hours=2100.0, priority_score=10.0,
                required_skill="Mechanical",
                maintenance_duration=60,
                last_maintenance_date=days(-25),
                next_maintenance_date=days(55),
            ),

            # ── Warning Machines ────────────────────────────────────────────────
            Machine(
                machine_code="MCH-008", name="Hydraulic Press #3",
                machine_type="Hydraulic Press", factory_section="Section B",
                status=MachineStatus.WARNING, risk_level=RiskLevel.MEDIUM,
                temperature=72.0, vibration=5.8, pressure=18.5,
                runtime_hours=8200.0, priority_score=45.0,
                required_skill="Hydraulics",
                maintenance_duration=120,
                last_maintenance_date=days(-90),
                next_maintenance_date=days(5),
            ),
            Machine(
                machine_code="MCH-009", name="Laser Cutter #2",
                machine_type="Laser System", factory_section="Section A",
                status=MachineStatus.WARNING, risk_level=RiskLevel.HIGH,
                temperature=68.0, vibration=4.2, pressure=0.0,
                runtime_hours=4500.0, priority_score=60.0,
                required_skill="Electronics",
                maintenance_duration=90,
                last_maintenance_date=days(-75),
                next_maintenance_date=days(2),
            ),
            Machine(
                machine_code="MCH-010", name="Paint Booth Exhaust System",
                machine_type="HVAC/Ventilation", factory_section="Section C",
                status=MachineStatus.WARNING, risk_level=RiskLevel.MEDIUM,
                temperature=58.0, vibration=6.1, pressure=2.8,
                runtime_hours=6700.0, priority_score=40.0,
                required_skill="Mechanical",
                maintenance_duration=75,
                last_maintenance_date=days(-60),
                next_maintenance_date=days(7),
            ),
            Machine(
                machine_code="MCH-011", name="Electric Motor Drive #4",
                machine_type="Electric Motor", factory_section="Section D",
                status=MachineStatus.WARNING, risk_level=RiskLevel.HIGH,
                temperature=78.0, vibration=7.2, pressure=0.0,
                runtime_hours=9800.0, priority_score=58.0,
                required_skill="Electrical",
                maintenance_duration=90,
                last_maintenance_date=days(-110),
                next_maintenance_date=days(3),
            ),

            # ── Critical Machines ───────────────────────────────────────────────
            Machine(
                machine_code="MCH-012", name="Injection Molding Machine #2",
                machine_type="Injection Molder", factory_section="Section B",
                status=MachineStatus.CRITICAL, risk_level=RiskLevel.CRITICAL,
                temperature=95.0, vibration=12.5, pressure=28.0,
                runtime_hours=12500.0, priority_score=95.0,
                required_skill="Hydraulics",
                maintenance_duration=180,
                last_maintenance_date=days(-120),
                next_maintenance_date=days(-2),     # overdue!
            ),
            Machine(
                machine_code="MCH-013", name="Heat Treatment Furnace #1",
                machine_type="Industrial Furnace", factory_section="Section C",
                status=MachineStatus.CRITICAL, risk_level=RiskLevel.CRITICAL,
                temperature=110.0, vibration=9.8, pressure=15.5,
                runtime_hours=7800.0, priority_score=92.0,
                required_skill="Instrumentation",
                maintenance_duration=150,
                last_maintenance_date=days(-95),
                next_maintenance_date=days(-1),     # overdue!
            ),
            Machine(
                machine_code="MCH-014", name="Stamping Press #1",
                machine_type="Stamping Press", factory_section="Section A",
                status=MachineStatus.UNDER_MAINTENANCE, risk_level=RiskLevel.HIGH,
                temperature=65.0, vibration=8.0, pressure=22.0,
                runtime_hours=6300.0, priority_score=70.0,
                required_skill="Mechanical",
                maintenance_duration=120,
                last_maintenance_date=days(-50),
                next_maintenance_date=days(0),
            ),
            Machine(
                machine_code="MCH-015", name="Cooling Tower System",
                machine_type="Cooling System", factory_section="Utility Room",
                status=MachineStatus.WARNING, risk_level=RiskLevel.MEDIUM,
                temperature=62.0, vibration=4.8, pressure=6.0,
                runtime_hours=11200.0, priority_score=48.0,
                required_skill="Mechanical",
                maintenance_duration=90,
                last_maintenance_date=days(-80),
                next_maintenance_date=days(4),
            ),
        ]
        db.add_all(machines)
        db.flush()
        print(f"   ✅ {len(machines)} machines created")

        # Shortcuts for FK references
        m = {m.machine_code: m for m in machines}
        t = {t.technician_code: t for t in technicians}

        # ── 3. MAINTENANCE HISTORY ─────────────────────────────────────────────
        history = [
            MaintenanceHistory(
                machine_id=m["MCH-001"].id, technician_id=t["TECH-001"].id,
                maintenance_date=days(-30),
                issue="Spindle bearing showing early wear signs",
                action_taken="Replaced spindle bearing, lubricated all joints, recalibrated",
                duration_minutes=90, notes="Next check in 60 days",
            ),
            MaintenanceHistory(
                machine_id=m["MCH-008"].id, technician_id=t["TECH-003"].id,
                maintenance_date=days(-90),
                issue="Hydraulic fluid leak at cylinder seal",
                action_taken="Replaced cylinder seal, topped up hydraulic fluid, tested pressure",
                duration_minutes=120, notes="Monitor pressure weekly",
            ),
            MaintenanceHistory(
                machine_id=m["MCH-012"].id, technician_id=t["TECH-003"].id,
                maintenance_date=days(-120),
                issue="Excessive vibration and overheating at high cycle rates",
                action_taken="Replaced injection unit, adjusted clamping force, cooled mold",
                duration_minutes=180, notes="Machine now showing critical signs again — urgent",
            ),
            MaintenanceHistory(
                machine_id=m["MCH-013"].id, technician_id=t["TECH-006"].id,
                maintenance_date=days(-95),
                issue="Temperature sensor failure causing erratic readings",
                action_taken="Replaced all thermocouples, recalibrated temperature controller",
                duration_minutes=150, notes="Furnace operating above safe limits now",
            ),
            MaintenanceHistory(
                machine_id=m["MCH-009"].id, technician_id=t["TECH-002"].id,
                maintenance_date=days(-75),
                issue="Laser head misalignment and lens contamination",
                action_taken="Cleaned and realigned laser head, replaced focusing lens",
                duration_minutes=90, notes="Cutting accuracy restored",
            ),
            MaintenanceHistory(
                machine_id=m["MCH-002"].id, technician_id=t["TECH-004"].id,
                maintenance_date=days(-15),
                issue="Routine joint lubrication and servo calibration",
                action_taken="Lubricated all 6 joints, updated servo PID parameters",
                duration_minutes=120, notes="Robot arm within spec",
            ),
            MaintenanceHistory(
                machine_id=m["MCH-014"].id, technician_id=t["TECH-001"].id,
                maintenance_date=days(-50),
                issue="Die misalignment causing part defects",
                action_taken="Re-aligned die set, replaced guide pins, adjusted stroke length",
                duration_minutes=120, notes="Machine placed under maintenance for further inspection",
            ),
            MaintenanceHistory(
                machine_id=m["MCH-011"].id, technician_id=t["TECH-002"].id,
                maintenance_date=days(-110),
                issue="Motor running hot — insulation degradation detected",
                action_taken="Replaced motor windings, tested insulation resistance",
                duration_minutes=90, notes="Motor approaching end-of-life — plan replacement",
            ),
        ]
        db.add_all(history)
        db.flush()
        print(f"   ✅ {len(history)} maintenance history records created")

        # ── 4. ALERTS ─────────────────────────────────────────────────────────
        alerts = [
            Alert(
                machine_id=m["MCH-012"].id,
                severity=AlertSeverity.CRITICAL,
                message="Injection Molding Machine #2 — Temperature 95°C exceeds critical threshold (90°C). "
                        "Vibration 12.5 mm/s is dangerously high. Maintenance overdue by 2 days.",
                recommended_action="Immediate shutdown and emergency maintenance. Assign senior technician.",
                status=AlertStatus.UNREAD,
            ),
            Alert(
                machine_id=m["MCH-013"].id,
                severity=AlertSeverity.CRITICAL,
                message="Heat Treatment Furnace #1 — Operating at 110°C, well above rated capacity. "
                        "Risk of thermal failure. Maintenance overdue.",
                recommended_action="Emergency maintenance required. Do not operate until inspected.",
                status=AlertStatus.UNREAD,
            ),
            Alert(
                machine_id=m["MCH-009"].id,
                severity=AlertSeverity.WARNING,
                message="Laser Cutter #2 — Temperature 68°C approaching warning threshold. "
                        "Runtime 4,500 hours since last service. Maintenance due in 2 days.",
                recommended_action="Schedule maintenance within 48 hours. Check laser alignment.",
                status=AlertStatus.UNREAD,
            ),
            Alert(
                machine_id=m["MCH-011"].id,
                severity=AlertSeverity.WARNING,
                message="Electric Motor Drive #4 — Motor temperature 78°C (limit: 80°C). "
                        "Vibration 7.2 mm/s indicates bearing wear. 9,800 runtime hours.",
                recommended_action="Schedule bearing replacement within 3 days.",
                status=AlertStatus.READ,
                read_at=hours(-2),
            ),
            Alert(
                machine_id=m["MCH-008"].id,
                severity=AlertSeverity.WARNING,
                message="Hydraulic Press #3 — Pressure reading 18.5 bar (normal: 15 bar). "
                        "Possible seal degradation. Scheduled maintenance in 5 days.",
                recommended_action="Check hydraulic seals and fluid level. Monitor closely.",
                status=AlertStatus.UNREAD,
            ),
        ]
        db.add_all(alerts)
        db.flush()
        print(f"   ✅ {len(alerts)} alerts created")

        # ── 5. MAINTENANCE TASKS ──────────────────────────────────────────────
        tasks = [
            MaintenanceTask(
                machine_id=m["MCH-012"].id, technician_id=t["TECH-001"].id,
                scheduled_date=days(0), start_time="08:00",
                duration_minutes=180,
                priority=TaskPriority.CRITICAL, status=TaskStatus.SCHEDULED,
                reason="Critical overheating and vibration — emergency maintenance",
            ),
            MaintenanceTask(
                machine_id=m["MCH-013"].id, technician_id=t["TECH-006"].id,
                scheduled_date=days(1), start_time="09:00",
                duration_minutes=150,
                priority=TaskPriority.CRITICAL, status=TaskStatus.PENDING,
                reason="Furnace temperature critical — overdue maintenance",
            ),
            MaintenanceTask(
                machine_id=m["MCH-009"].id, technician_id=t["TECH-002"].id,
                scheduled_date=days(2), start_time="10:00",
                duration_minutes=90,
                priority=TaskPriority.HIGH, status=TaskStatus.SCHEDULED,
                reason="Laser head alignment check — due within 48 hours",
            ),
            MaintenanceTask(
                machine_id=m["MCH-011"].id, technician_id=t["TECH-002"].id,
                scheduled_date=days(3), start_time="08:00",
                duration_minutes=90,
                priority=TaskPriority.HIGH, status=TaskStatus.PENDING,
                reason="Bearing replacement — motor temperature near limit",
            ),
            MaintenanceTask(
                machine_id=m["MCH-015"].id, technician_id=t["TECH-003"].id,
                scheduled_date=days(4), start_time="13:00",
                duration_minutes=90,
                priority=TaskPriority.MEDIUM, status=TaskStatus.PENDING,
                reason="Routine cooling tower inspection — 80 days since last service",
            ),
        ]
        db.add_all(tasks)
        db.flush()
        print(f"   ✅ {len(tasks)} maintenance tasks created")

        # ── 6. RULES ──────────────────────────────────────────────────────────
        rules = [
            Rule(
                name="Critical Temperature Alert",
                description="Trigger critical alert when machine temperature exceeds 90°C",
                condition="machine.temperature > 90",
                action="set_status(CRITICAL); create_alert(CRITICAL, 'Temperature exceeded 90°C'); set_priority(CRITICAL)",
                severity=RuleSeverity.CRITICAL, enabled=True,
            ),
            Rule(
                name="High Vibration Warning",
                description="Trigger warning when vibration exceeds 8 mm/s",
                condition="machine.vibration > 8",
                action="set_risk(HIGH); create_alert(WARNING, 'High vibration detected'); schedule_maintenance(priority=HIGH)",
                severity=RuleSeverity.HIGH, enabled=True,
            ),
            Rule(
                name="Overdue Maintenance Escalation",
                description="Escalate priority if next_maintenance_date has passed",
                condition="machine.next_maintenance_date < now()",
                action="set_priority_score(priority_score + 30); create_alert(CRITICAL, 'Maintenance overdue')",
                severity=RuleSeverity.CRITICAL, enabled=True,
            ),
            Rule(
                name="Long Runtime Warning",
                description="Flag machines running over 10,000 hours without major service",
                condition="machine.runtime_hours > 10000",
                action="set_risk(HIGH); create_alert(WARNING, 'Machine exceeded 10,000 runtime hours')",
                severity=RuleSeverity.MEDIUM, enabled=True,
            ),
            Rule(
                name="High Pressure Alert",
                description="Alert when hydraulic/pneumatic pressure exceeds 25 bar",
                condition="machine.pressure > 25",
                action="create_alert(CRITICAL, 'Pressure exceeds safe limit of 25 bar'); set_status(CRITICAL)",
                severity=RuleSeverity.HIGH, enabled=True,
            ),
        ]
        db.add_all(rules)
        db.flush()
        print(f"   ✅ {len(rules)} rules created")

        db.commit()
        print("\n🎉 Seed complete! Summary:")
        print(f"   Machines:    {db.query(Machine).count()}")
        print(f"   Technicians: {db.query(Technician).count()}")
        print(f"   Tasks:       {db.query(MaintenanceTask).count()}")
        print(f"   History:     {db.query(MaintenanceHistory).count()}")
        print(f"   Alerts:      {db.query(Alert).count()}")
        print(f"   Rules:       {db.query(Rule).count()}")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
