import os
import sys
import json
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from config import Config, DEFAULT_DB_PATH
from app.models.schema import (
    Base, User, Zone, Handler, Report, RoutingRule,
    Assignment, StatusHistory, DispatchLog, ClassificationLog
)

def seed_database(db_path=DEFAULT_DB_PATH):
    print(f"[*] Seeding database at: {db_path}")
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # If users exist, skip seeding to avoid duplicate data
    if session.query(User).count() > 0:
        print("[!] Database already contains data. Skipping re-seed.")
        session.close()
        return

    # 1. Seed Users
    print("[*] Creating Users...")
    users_data = [
        ("admin", "AdminPassword123!", "admin", "System Administrator", "admin@trafficops.gov", "+1-555-0199"),
        ("handler1", "HandlerPassword123!", "handler", "Alex Carter - Signal Tech", "alex.carter@trafficops.gov", "+1-555-0101"),
        ("handler2", "HandlerPassword123!", "handler", "Priya Sharma - Electrical Lead", "priya.sharma@trafficops.gov", "+1-555-0102"),
        ("handler3", "HandlerPassword123!", "handler", "David Kim - Sensor Specialist", "david.kim@trafficops.gov", "+1-555-0103"),
        ("handler4", "HandlerPassword123!", "handler", "Elena Rostova - Network Tech", "elena.rostova@trafficops.gov", "+1-555-0104"),
        ("handler5", "HandlerPassword123!", "handler", "Marcus Vance - Highway Rapid", "marcus.vance@trafficops.gov", "+1-555-0105"),
        ("reporter", "ReporterPassword123!", "reporter", "Officer Johnathan Reed", "jreed@police.gov", "+1-555-0188")
    ]
    for username, pwd, role, name, email, phone in users_data:
        u = User(
            username=username,
            password_hash=generate_password_hash(pwd),
            role=role,
            full_name=name,
            email=email,
            phone=phone
        )
        session.add(u)
    session.commit()

    # 2. Seed Zones
    print("[*] Creating Zones...")
    zones_data = [
        ("ZONE-A", "Downtown / Central Metro", "High-density pedestrian and vehicular traffic area including civic center."),
        ("ZONE-B", "North Commercial Corridor", "Commercial shopping hubs, shopping complexes, and transit junctions."),
        ("ZONE-C", "East Highway & Interchange", "High-speed expressway exits, ring road, and arterial interchange."),
        ("ZONE-D", "South Industrial Hub", "Freight terminals, manufacturing plants, and heavy container transport roads."),
        ("ZONE-E", "West Residential & School", "Residential suburban streets, school crossings, and community hospitals.")
    ]
    zones_dict = {}
    for code, name, desc in zones_data:
        z = Zone(zone_code=code, name=name, description=desc, is_active=True)
        session.add(z)
        session.flush()
        zones_dict[code] = z
    session.commit()

    # 3. Seed Maintenance Handlers
    print("[*] Creating Handlers...")
    categories = Config.FAULT_CATEGORIES
    handlers_data = [
        ("HND-001", "Alex Carter", "alex.carter@trafficops.gov", "+1-555-0101", "ZONE-A", [categories[0], categories[1]], True, 5, 0, True),
        ("HND-002", "Priya Sharma", "priya.sharma@trafficops.gov", "+1-555-0102", "ZONE-A", [categories[2], categories[0]], True, 4, 0, True),
        ("HND-003", "David Kim", "david.kim@trafficops.gov", "+1-555-0103", "ZONE-B", [categories[3], categories[1]], True, 4, 0, True),
        ("HND-004", "Elena Rostova", "elena.rostova@trafficops.gov", "+1-555-0104", "ZONE-B", [categories[4], categories[2]], True, 4, 0, True),
        ("HND-005", "Marcus Vance", "marcus.vance@trafficops.gov", "+1-555-0105", "ZONE-C", [categories[0], categories[1], categories[2]], True, 5, 0, True),
        ("HND-006", "Sarah Jenkins", "sarah.jenkins@trafficops.gov", "+1-555-0106", "ZONE-D", [categories[2], categories[3]], True, 4, 0, True),
        ("HND-007", "Carlos Mendez", "carlos.mendez@trafficops.gov", "+1-555-0107", "ZONE-E", [categories[0], categories[3]], True, 4, 0, True),
        ("HND-008", "Rapid Response Squad", "rapid.dispatch@trafficops.gov", "+1-555-0199", "ZONE-C", categories, True, 10, 0, True)
    ]
    handlers_dict = {}
    for code, name, email, phone, z_code, cats, avail, max_c, cur_w, backup_elig in handlers_data:
        h = Handler(
            handler_code=code,
            name=name,
            email=email,
            phone=phone,
            zone_id=zones_dict[z_code].id,
            is_available=avail,
            max_capacity=max_c,
            current_workload=cur_w,
            is_backup_eligible=backup_elig
        )
        h.set_supported_categories(cats)
        session.add(h)
        session.flush()
        handlers_dict[code] = h
    session.commit()

    # 4. Seed Routing Rules
    print("[*] Creating 25 Zone-Category Routing Rules...")
    # Mapping table rules for 5 zones x 5 categories
    rule_mappings = [
        # ZONE A
        ("ZONE-A", categories[0], "HND-001", "HND-002", "SUPERVISOR_RAPID_ESCALATION"),
        ("ZONE-A", categories[1], "HND-001", "HND-005", "SUPERVISOR_RAPID_ESCALATION"),
        ("ZONE-A", categories[2], "HND-002", "HND-008", "CHIEF_ELECTRICAL_ESCALATION"),
        ("ZONE-A", categories[3], "HND-003", "HND-007", "SUPERVISOR_RAPID_ESCALATION"),
        ("ZONE-A", categories[4], "HND-004", "HND-008", "NETWORK_NOC_ESCALATION"),

        # ZONE B
        ("ZONE-B", categories[0], "HND-001", "HND-005", "SUPERVISOR_RAPID_ESCALATION"),
        ("ZONE-B", categories[1], "HND-003", "HND-001", "SUPERVISOR_RAPID_ESCALATION"),
        ("ZONE-B", categories[2], "HND-004", "HND-002", "CHIEF_ELECTRICAL_ESCALATION"),
        ("ZONE-B", categories[3], "HND-003", "HND-006", "SUPERVISOR_RAPID_ESCALATION"),
        ("ZONE-B", categories[4], "HND-004", "HND-008", "NETWORK_NOC_ESCALATION"),

        # ZONE C
        ("ZONE-C", categories[0], "HND-005", "HND-008", "HIGHWAY_PATROL_ESCALATION"),
        ("ZONE-C", categories[1], "HND-005", "HND-001", "HIGHWAY_PATROL_ESCALATION"),
        ("ZONE-C", categories[2], "HND-005", "HND-002", "HIGHWAY_PATROL_ESCALATION"),
        ("ZONE-C", categories[3], "HND-006", "HND-003", "SUPERVISOR_RAPID_ESCALATION"),
        ("ZONE-C", categories[4], "HND-008", "HND-004", "NETWORK_NOC_ESCALATION"),

        # ZONE D
        ("ZONE-D", categories[0], "HND-005", "HND-006", "INDUSTRIAL_DISPATCH_ESCALATION"),
        ("ZONE-D", categories[1], "HND-001", "HND-005", "INDUSTRIAL_DISPATCH_ESCALATION"),
        ("ZONE-D", categories[2], "HND-006", "HND-002", "CHIEF_ELECTRICAL_ESCALATION"),
        ("ZONE-D", categories[3], "HND-006", "HND-007", "INDUSTRIAL_DISPATCH_ESCALATION"),
        ("ZONE-D", categories[4], "HND-004", "HND-008", "NETWORK_NOC_ESCALATION"),

        # ZONE E
        ("ZONE-E", categories[0], "HND-007", "HND-001", "COMMUNITY_SAFETY_ESCALATION"),
        ("ZONE-E", categories[1], "HND-001", "HND-003", "COMMUNITY_SAFETY_ESCALATION"),
        ("ZONE-E", categories[2], "HND-002", "HND-006", "CHIEF_ELECTRICAL_ESCALATION"),
        ("ZONE-E", categories[3], "HND-007", "HND-003", "COMMUNITY_SAFETY_ESCALATION"),
        ("ZONE-E", categories[4], "HND-004", "HND-008", "NETWORK_NOC_ESCALATION"),
    ]

    for z_code, cat, prim_code, back_code, esc in rule_mappings:
        rule = RoutingRule(
            zone_id=zones_dict[z_code].id,
            category=cat,
            primary_handler_id=handlers_dict[prim_code].id,
            backup_handler_id=handlers_dict[back_code].id if back_code else None,
            escalation_path=esc,
            is_active=True
        )
        session.add(rule)
    session.commit()

    # 5. Seed Realistic Demonstration Reports across All Categories & Statuses
    print("[*] Creating Seed Reports & History...")
    now = datetime.utcnow()
    reports_seed = [
        {
            "code": "TSF-2026-00001",
            "name": "Jane Doe",
            "contact": "+1-555-4321",
            "sig_id": "SIG-ZONA-101",
            "zone_code": "ZONE-A",
            "location": "Main St & 4th Ave Intersection",
            "desc": "Northbound red light not working; bulb completely burnt out causing near miss.",
            "category": categories[0],
            "priority": "HIGH",
            "status": "ASSIGNED",
            "handler_code": "HND-001",
            "days_ago": 2
        },
        {
            "code": "TSF-2026-00002",
            "name": "Officer Miller",
            "contact": "+1-555-8765",
            "sig_id": "SIG-ZONB-205",
            "zone_code": "ZONE-B",
            "location": "Market Blvd & 12th St",
            "desc": "Unexpected signal switching and wrong timing duration. Green light only stays on for 3 seconds.",
            "category": categories[1],
            "priority": "MEDIUM",
            "status": "IN_PROGRESS",
            "handler_code": "HND-003",
            "days_ago": 3
        },
        {
            "code": "TSF-2026-00003",
            "name": "Captain Rogers",
            "contact": "+1-555-9012",
            "sig_id": "SIG-ZONC-310",
            "zone_code": "ZONE-C",
            "location": "Interstate 80 Eastbound Ramp",
            "desc": "Controller cabinet power supply failure; breaker tripped and signal is dead.",
            "category": categories[2],
            "priority": "EMERGENCY",
            "status": "ASSIGNED",
            "handler_code": "HND-005",
            "days_ago": 1
        },
        {
            "code": "TSF-2026-00004",
            "name": "Sarah Connor",
            "contact": "+1-555-3456",
            "sig_id": "SIG-ZONE-502",
            "zone_code": "ZONE-E",
            "location": "Oak Tree Elementary Crossing",
            "desc": "Pedestrian sensor push button stuck and unresponsive; crosswalk walk sign does not activate.",
            "category": categories[3],
            "priority": "MEDIUM",
            "status": "RESOLVED",
            "handler_code": "HND-007",
            "days_ago": 4,
            "resolution": "Replaced physical actuator switch in push button housing and re-tested actuation cycle."
        },
        {
            "code": "TSF-2026-00005",
            "name": "NOC Dispatcher",
            "contact": "+1-555-6789",
            "sig_id": "SIG-ZOND-415",
            "zone_code": "ZONE-D",
            "location": "Harbor Terminal Gateway & Pier 4",
            "desc": "Central server communication failure; remote monitoring link lost due to cellular modem timeout.",
            "category": categories[4],
            "priority": "LOW",
            "status": "ASSIGNED",
            "handler_code": "HND-004",
            "days_ago": 1
        },
        {
            "code": "TSF-2026-00006",
            "name": "Marcus Kane",
            "contact": "+1-555-5544",
            "sig_id": "SIG-ZONA-108",
            "zone_code": "ZONE-A",
            "location": "Broad St & 7th Ave",
            "desc": "All lights switched off completely; intersection is pitch dark and dangerous.",
            "category": categories[0],
            "priority": "EMERGENCY",
            "status": "ESCALATED",
            "handler_code": None,
            "days_ago": 0
        },
        {
            "code": "TSF-2026-00007",
            "name": "Traffic Warden Lee",
            "contact": "+1-555-7788",
            "sig_id": "SIG-ZONB-222",
            "zone_code": "ZONE-B",
            "location": "Central Plaza Circle",
            "desc": "Vehicle detection sensor loop failure in lane 2; queue not recognized by phase controller.",
            "category": categories[3],
            "priority": "MEDIUM",
            "status": "PENDING",
            "handler_code": None,
            "days_ago": 0
        }
    ]

    for item in reports_seed:
        r_created = now - timedelta(days=item["days_ago"], hours=item.get("hours", 3))
        rep = Report(
            report_code=item["code"],
            reporter_name=item["name"],
            reporter_contact=item["contact"],
            signal_id=item["sig_id"],
            zone_id=zones_dict[item["zone_code"]].id,
            zone_raw=item["zone_code"],
            location=item["location"],
            description=item["desc"],
            category=item["category"],
            priority=item["priority"],
            status=item["status"],
            created_at=r_created,
            updated_at=now
        )
        session.add(rep)
        session.flush()

        # Classification log
        cl = ClassificationLog(
            report_id=rep.id,
            detected_category=item["category"],
            matched_categories=json.dumps([item["category"]]),
            confidence_score=0.95,
            resolution_rule="Matched standard keyword rules.",
            is_manual_override=False,
            timestamp=r_created
        )
        session.add(cl)

        # Status history
        sh1 = StatusHistory(
            report_id=rep.id,
            previous_status=None,
            new_status="SUBMITTED",
            updated_by=item["name"],
            remarks="Initial report submitted via web portal.",
            created_at=r_created
        )
        session.add(sh1)

        if item["status"] != "SUBMITTED":
            sh2 = StatusHistory(
                report_id=rep.id,
                previous_status="SUBMITTED",
                new_status=item["status"],
                updated_by="SYSTEM_DISPATCHER",
                remarks=f"Report transitioned to {item['status']}.",
                created_at=r_created + timedelta(minutes=2)
            )
            session.add(sh2)

        # Assignment
        if item.get("handler_code"):
            hnd = handlers_dict[item["handler_code"]]
            hnd.current_workload += 1
            asg_status = "COMPLETED" if item["status"] == "RESOLVED" else "ACTIVE"
            asg = Assignment(
                report_id=rep.id,
                handler_id=hnd.id,
                assigned_at=r_created + timedelta(minutes=2),
                status=asg_status,
                assignment_type="PRIMARY",
                completed_at=now if item["status"] == "RESOLVED" else None,
                resolution_notes=item.get("resolution")
            )
            session.add(asg)

            dl = DispatchLog(
                report_id=rep.id,
                decision="ASSIGNED_PRIMARY",
                reason=f"Assigned to primary zone handler {hnd.name}.",
                primary_handler_id=hnd.id,
                assigned_handler_id=hnd.id,
                is_backup=False,
                is_escalated=False,
                is_queued=False,
                timestamp=r_created + timedelta(minutes=2)
            )
            session.add(dl)
        elif item["status"] == "ESCALATED":
            asg = Assignment(
                report_id=rep.id,
                handler_id=None,
                assigned_at=r_created + timedelta(minutes=1),
                status="ACTIVE",
                assignment_type="ESCALATION"
            )
            session.add(asg)
            dl = DispatchLog(
                report_id=rep.id,
                decision="ESCALATED_EMERGENCY",
                reason="Immediate escalation: All primary handlers busy or emergency override.",
                primary_handler_id=None,
                assigned_handler_id=None,
                is_backup=False,
                is_escalated=True,
                is_queued=False,
                timestamp=r_created + timedelta(minutes=1)
            )
            session.add(dl)
        elif item["status"] == "PENDING":
            dl = DispatchLog(
                report_id=rep.id,
                decision="QUEUED_CAPACITY",
                reason="Placed in waiting queue awaiting handler capacity.",
                primary_handler_id=None,
                assigned_handler_id=None,
                is_backup=False,
                is_escalated=False,
                is_queued=True,
                timestamp=r_created + timedelta(minutes=1)
            )
            session.add(dl)

    session.commit()
    session.close()
    print("[+] Database seeding completed successfully with 5 zones, 8 handlers, 25 routing rules, and realistic test reports.")

if __name__ == "__main__":
    seed_database()
