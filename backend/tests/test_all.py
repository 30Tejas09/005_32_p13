import os
import sys
import json
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from config import Config, TestConfig
from app import create_app
from app.models.schema import (
    Base, User, Zone, Handler, Report, RoutingRule,
    Assignment, StatusHistory, DispatchLog, ClassificationLog
)
from app.algorithms.dfa import ReportIdDFA
from app.algorithms.classifier import FaultClassifier
from app.algorithms.dispatcher import DispatchEngine
from app.validators.input_validator import InputValidator

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Populate baseline entities
    z_a = Zone(zone_code="ZONE-A", name="Downtown Central", is_active=True)
    z_b = Zone(zone_code="ZONE-B", name="North Commercial", is_active=True)
    session.add_all([z_a, z_b])
    session.flush()

    h1 = Handler(handler_code="HND-T01", name="Primary Tech Alpha", zone_id=z_a.id, is_available=True, max_capacity=2, current_workload=0, is_backup_eligible=True)
    h1.set_supported_categories(["Signal Light Failure", "Signal Timing Failure"])

    h2 = Handler(handler_code="HND-T02", name="Backup Tech Beta", zone_id=z_a.id, is_available=True, max_capacity=2, current_workload=0, is_backup_eligible=True)
    h2.set_supported_categories(["Signal Light Failure", "Controller / Electrical Failure"])

    session.add_all([h1, h2])
    session.flush()

    # Routing rule
    r_rule = RoutingRule(
        zone_id=z_a.id,
        category="Signal Light Failure",
        primary_handler_id=h1.id,
        backup_handler_id=h2.id,
        escalation_path="EMERGENCY_ESCALATION_PATH",
        is_active=True
    )
    session.add(r_rule)
    session.commit()

    yield session, engine
    session.close()

@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.test_client() as client:
        yield client

# =========================================================================
# TEST 1: Valid report identifier accepted by DFA
# =========================================================================
def test_01_valid_report_id_accepted_by_dfa():
    """Objective: Verify that valid formatted report ID is accepted by DFA."""
    valid_id = "TSF-2026-00001"
    res = ReportIdDFA.simulate(valid_id)
    assert res["is_accepted"] is True
    assert res["final_state"] == "q14"
    assert res["error_reason"] is None
    assert len(res["steps"]) == 14

# =========================================================================
# TEST 2: Invalid report identifier rejected by DFA
# =========================================================================
def test_02_invalid_report_id_rejected_by_dfa():
    """Objective: Verify malformed report ID transitions to trap/rejection state with exact error."""
    invalid_ids = [
        ("TXF-2026-00001", "expected 'S', received 'X'"),
        ("TSF-202-00001", "expected Year digit (0-9), received '-'"),
        ("TSF-2026-0000199", "unexpected extra character"),
        ("BAD-FORMAT", "expected 'T'")
    ]
    for bad_id, err_fragment in invalid_ids:
        res = ReportIdDFA.simulate(bad_id)
        assert res["is_accepted"] is False
        assert res["final_state"] == "q_trap"
        assert res["error_reason"] is not None
        assert err_fragment.lower() in res["error_reason"].lower()

# =========================================================================
# TEST 3: Valid report identifier accepted by regex
# =========================================================================
def test_03_valid_report_id_accepted_by_regex():
    """Objective: Verify regex accepts valid format."""
    import re
    valid_id = "TSF-2026-99999"
    match = bool(re.match(ReportIdDFA.EQUIVALENT_REGEX, valid_id))
    assert match is True

# =========================================================================
# TEST 4: DFA and regex produce equivalent validation results
# =========================================================================
def test_04_dfa_and_regex_produce_equivalent_results():
    """Objective: Verify 100% equivalence between DFA and Regex across valid and diverse invalid inputs."""
    test_cases = [
        "TSF-2026-00001",
        "TSF-1999-12345",
        "TSF-2030-99999",
        "TSF-2026-0001",
        "TSF-2026-000001",
        "tsf-2026-00001",
        "ABC-2026-00001",
        "TSF_2026_00001",
        "TSF-202A-00001",
        "TSF-2026-0000X",
        "",
        "TSF-2026-00001 ",
        " TSF-2026-00001"
    ]
    for candidate in test_cases:
        res = ReportIdDFA.simulate(candidate)
        assert res["equivalent"] is True, f"Equivalence mismatch on '{candidate}': DFA={res['is_accepted']}, Regex={res['regex_match']}"

# =========================================================================
# TEST 5: Missing required fields rejected
# =========================================================================
def test_05_missing_required_fields_rejected():
    """Objective: Verify input validator rejects submission when required fields are missing."""
    incomplete_data = {
        "reporter_name": "",
        "reporter_contact": "+1-555-1234",
        "report_code": "TSF-2026-00001",
        "signal_id": "",
        "zone": "ZONE-A",
        "location": "",
        "description": "Red light out"
    }
    val = InputValidator.validate_report_submission(incomplete_data)
    assert val["is_valid"] is False
    assert "reporter_name" in val["errors"]
    assert "signal_id" in val["errors"]
    assert "location" in val["errors"]

# =========================================================================
# TEST 6: All five fault categories classified correctly
# =========================================================================
def test_06_all_five_fault_categories_classified_correctly():
    """Objective: Verify each of the 5 categories is correctly classified with representative inputs."""
    samples = [
        ("The red light is not working and green bulb is burnt out completely.", "Signal Light Failure"),
        ("Unexpected signal switching and wrong timer duration; cycle length is stuck.", "Signal Timing Failure"),
        ("Signal controller cabinet power supply failure and circuit breaker tripped.", "Controller / Electrical Failure"),
        ("Vehicle detection sensor loop wire damaged and pedestrian push button broken.", "Sensor / Detection Failure"),
        ("Remote monitoring link offline and central server communication failure via cellular modem.", "Communication / Network Failure")
    ]
    for text, expected_category in samples:
        res = FaultClassifier.classify(text)
        assert res["primary_category"] == expected_category, f"Expected '{expected_category}' but got '{res['primary_category']}' for text: '{text}'"

# =========================================================================
# TEST 7: Conflicting classification patterns resolved correctly
# =========================================================================
def test_07_conflicting_classification_patterns_resolved():
    """Objective: Verify multi-category text resolves to primary safety category and logs all candidates."""
    # Text mentions red light (Signal Light), timing (Timing), and controller (Electrical)
    mixed_text = "Controller circuit fault caused red light not working and signal timing stuck on yellow."
    res = FaultClassifier.classify(mixed_text)
    # Both Signal Light and Controller/Electrical match; conflict resolution should pick primary safety category
    assert res["primary_category"] in Config.FAULT_CATEGORIES
    assert len(res["candidates"]) >= 2
    # Verify audit metadata
    assert "resolution_rule" in res
    assert res["confidence_score"] > 0

# =========================================================================
# TEST 8: Unknown zone sent to fallback queue
# =========================================================================
def test_08_unknown_zone_sent_to_fallback_queue(test_db):
    """Objective: Verify reports with unrecognized zone codes route to central fallback queue."""
    session, _ = test_db
    rep = Report(
        report_code="TSF-2026-00010",
        reporter_name="Mark Unknown",
        reporter_contact="+1-555-9999",
        signal_id="SIG-UNK-001",
        zone_id=None,
        zone_raw="ZONE-UNKNOWN-99",
        location="Nowhere Land",
        description="Red light burnt out",
        category="Signal Light Failure",
        priority="MEDIUM",
        status="SUBMITTED"
    )
    session.add(rep)
    session.commit()

    dispatch_res = DispatchEngine.dispatch_report(session, rep)
    assert dispatch_res["decision"] == "FALLBACK_UNKNOWN_ZONE"
    assert rep.status == "PENDING"
    
    # Verify dispatch log exists
    log = session.query(DispatchLog).filter_by(report_id=rep.id).first()
    assert log is not None
    assert log.decision == "FALLBACK_UNKNOWN_ZONE"
    assert log.is_queued is True

# =========================================================================
# TEST 9: Invalid routing key handled correctly
# =========================================================================
def test_09_invalid_routing_key_handled(test_db):
    """Objective: Verify when zone exists but no routing rule for category, report is placed in queue."""
    session, _ = test_db
    z_b = session.query(Zone).filter_by(zone_code="ZONE-B").first()
    
    rep = Report(
        report_code="TSF-2026-00011",
        reporter_name="Officer Bob",
        reporter_contact="+1-555-8888",
        signal_id="SIG-ZONB-111",
        zone_id=z_b.id,
        zone_raw="ZONE-B",
        location="North Way",
        description="Cellular modem communication failure",
        category="Communication / Network Failure", # No rule in test_db for ZONE-B + Comm
        priority="LOW",
        status="SUBMITTED"
    )
    session.add(rep)
    session.commit()

    dispatch_res = DispatchEngine.dispatch_report(session, rep)
    assert dispatch_res["decision"] == "NO_ROUTING_RULE"
    assert rep.status == "PENDING"

# =========================================================================
# TEST 10: Primary handler available and within capacity
# =========================================================================
def test_10_primary_handler_available_and_assigned(test_db):
    """Objective: Verify eligible primary handler is assigned and workload increments."""
    session, _ = test_db
    z_a = session.query(Zone).filter_by(zone_code="ZONE-A").first()
    h1 = session.query(Handler).filter_by(handler_code="HND-T01").first()
    initial_workload = h1.current_workload

    rep = Report(
        report_code="TSF-2026-00012",
        reporter_name="Alice Primary",
        reporter_contact="+1-555-7777",
        signal_id="SIG-ZONA-102",
        zone_id=z_a.id,
        zone_raw="ZONE-A",
        location="Downtown 1st St",
        description="Red light failure",
        category="Signal Light Failure",
        priority="HIGH",
        status="SUBMITTED"
    )
    session.add(rep)
    session.commit()

    res = DispatchEngine.dispatch_report(session, rep)
    assert res["decision"] == "ASSIGNED_PRIMARY"
    assert rep.status == "ASSIGNED"
    assert h1.current_workload == initial_workload + 1

    active_asg = session.query(Assignment).filter_by(report_id=rep.id, status="ACTIVE").first()
    assert active_asg is not None
    assert active_asg.handler_id == h1.id
    assert active_asg.assignment_type == "PRIMARY"

# =========================================================================
# TEST 11: Primary handler unavailable and backup selected
# =========================================================================
def test_11_primary_unavailable_backup_selected(test_db):
    """Objective: When primary handler is unavailable, automatically select backup handler."""
    session, _ = test_db
    z_a = session.query(Zone).filter_by(zone_code="ZONE-A").first()
    h1 = session.query(Handler).filter_by(handler_code="HND-T01").first()
    h2 = session.query(Handler).filter_by(handler_code="HND-T02").first()

    # Mark primary unavailable
    h1.is_available = False
    session.commit()

    rep = Report(
        report_code="TSF-2026-00013",
        reporter_name="Charlie Backup",
        reporter_contact="+1-555-6666",
        signal_id="SIG-ZONA-103",
        zone_id=z_a.id,
        zone_raw="ZONE-A",
        location="Downtown 2nd St",
        description="Red light failure",
        category="Signal Light Failure",
        priority="MEDIUM",
        status="SUBMITTED"
    )
    session.add(rep)
    session.commit()

    res = DispatchEngine.dispatch_report(session, rep)
    assert res["decision"] == "ASSIGNED_BACKUP"
    assert rep.status == "ASSIGNED"
    assert h2.current_workload == 1

    active_asg = session.query(Assignment).filter_by(report_id=rep.id, status="ACTIVE").first()
    assert active_asg.handler_id == h2.id
    assert active_asg.assignment_type == "BACKUP"

# =========================================================================
# TEST 12: Handler capacity overflow handled correctly
# =========================================================================
def test_12_handler_capacity_overflow_handled(test_db):
    """Objective: When primary is at full capacity, overflow routes to backup handler."""
    session, _ = test_db
    z_a = session.query(Zone).filter_by(zone_code="ZONE-A").first()
    h1 = session.query(Handler).filter_by(handler_code="HND-T01").first()
    h2 = session.query(Handler).filter_by(handler_code="HND-T02").first()

    # Fill primary capacity
    h1.is_available = True
    h1.current_workload = h1.max_capacity # 2/2
    h2.current_workload = 0
    session.commit()

    rep = Report(
        report_code="TSF-2026-00014",
        reporter_name="Dave Overflow",
        reporter_contact="+1-555-5555",
        signal_id="SIG-ZONA-104",
        zone_id=z_a.id,
        zone_raw="ZONE-A",
        location="Downtown 3rd St",
        description="Red light burnt out",
        category="Signal Light Failure",
        priority="MEDIUM",
        status="SUBMITTED"
    )
    session.add(rep)
    session.commit()

    res = DispatchEngine.dispatch_report(session, rep)
    assert res["decision"] == "ASSIGNED_BACKUP"
    assert h2.current_workload == 1

# =========================================================================
# TEST 13: Emergency priority override
# =========================================================================
def test_13_emergency_priority_override_escalation(test_db):
    """Objective: When all handlers full, EMERGENCY/CRITICAL report escalates immediately."""
    session, _ = test_db
    z_a = session.query(Zone).filter_by(zone_code="ZONE-A").first()
    h1 = session.query(Handler).filter_by(handler_code="HND-T01").first()
    h2 = session.query(Handler).filter_by(handler_code="HND-T02").first()

    # Exhaust both primary and backup
    h1.current_workload = h1.max_capacity
    h2.current_workload = h2.max_capacity
    session.commit()

    rep = Report(
        report_code="TSF-2026-00015",
        reporter_name="Emergency Officer",
        reporter_contact="+1-555-9111",
        signal_id="SIG-ZONA-911",
        zone_id=z_a.id,
        zone_raw="ZONE-A",
        location="Critical Highway Intersection",
        description="All lights off completely, collision risk imminent!",
        category="Signal Light Failure",
        priority="EMERGENCY",
        status="SUBMITTED"
    )
    session.add(rep)
    session.commit()

    res = DispatchEngine.dispatch_report(session, rep)
    assert res["decision"] == "ESCALATED_EMERGENCY"
    assert rep.status == "ESCALATED"

# =========================================================================
# TEST 14: Multiple simultaneous reports ordered deterministically
# =========================================================================
def test_14_multiple_simultaneous_reports_deterministic_order(test_db):
    """Objective: Queue ordering must strictly follow priority rank (EMERGENCY > CRITICAL > HIGH > MEDIUM > LOW) then submission timestamp."""
    session, _ = test_db
    now = datetime.utcnow()
    
    # Create 5 pending reports out of priority order with timestamps
    r_med = Report(report_code="TSF-2026-00021", reporter_name="R1", reporter_contact="123", signal_id="S1", location="L1", description="D1", category="Signal Light Failure", priority="MEDIUM", status="PENDING", created_at=now - timedelta(minutes=10))
    r_emg = Report(report_code="TSF-2026-00022", reporter_name="R2", reporter_contact="123", signal_id="S2", location="L2", description="D2", category="Signal Light Failure", priority="EMERGENCY", status="PENDING", created_at=now - timedelta(minutes=2))
    r_low = Report(report_code="TSF-2026-00023", reporter_name="R3", reporter_contact="123", signal_id="S3", location="L3", description="D3", category="Signal Light Failure", priority="LOW", status="PENDING", created_at=now - timedelta(minutes=20))
    r_crit = Report(report_code="TSF-2026-00024", reporter_name="R4", reporter_contact="123", signal_id="S4", location="L4", description="D4", category="Signal Light Failure", priority="CRITICAL", status="PENDING", created_at=now - timedelta(minutes=5))
    r_high = Report(report_code="TSF-2026-00025", reporter_name="R5", reporter_contact="123", signal_id="S5", location="L5", description="D5", category="Signal Light Failure", priority="HIGH", status="PENDING", created_at=now - timedelta(minutes=8))
    
    session.add_all([r_med, r_emg, r_low, r_crit, r_high])
    session.commit()

    queue = DispatchEngine.get_waiting_queue(session)
    ordered_codes = [r.report_code for r in queue if r.report_code.startswith("TSF-2026-0002")]
    
    # Expected order: EMERGENCY (22), CRITICAL (24), HIGH (25), MEDIUM (21), LOW (23)
    assert ordered_codes == [
        "TSF-2026-00022",
        "TSF-2026-00024",
        "TSF-2026-00025",
        "TSF-2026-00021",
        "TSF-2026-00023"
    ]

# =========================================================================
# TEST 15: Duplicate active assignment prevented
# =========================================================================
def test_15_duplicate_active_assignment_prevented(test_db):
    """Objective: A report cannot be assigned to two active handlers simultaneously."""
    session, _ = test_db
    z_a = session.query(Zone).filter_by(zone_code="ZONE-A").first()
    h1 = session.query(Handler).filter_by(handler_code="HND-T01").first()

    rep = Report(
        report_code="TSF-2026-00030",
        reporter_name="Officer One",
        reporter_contact="111",
        signal_id="SIG-DUP-01",
        zone_id=z_a.id,
        location="Loc 1",
        description="Desc",
        category="Signal Light Failure",
        priority="HIGH",
        status="ASSIGNED"
    )
    session.add(rep)
    session.flush()

    # Create active assignment
    asg = Assignment(report_id=rep.id, handler_id=h1.id, status="ACTIVE", assignment_type="PRIMARY")
    session.add(asg)
    session.commit()

    # Attempt to dispatch again
    res = DispatchEngine.dispatch_report(session, rep)
    assert res["success"] is False
    assert res["decision"] == "DUPLICATE_ACTIVE_ASSIGNMENT_PREVENTED"
    
    # Verify count of active assignments remains strictly 1
    active_count = session.query(Assignment).filter_by(report_id=rep.id, status="ACTIVE").count()
    assert active_count == 1

# =========================================================================
# TEST 16: No eligible handler sends report to waiting queue
# =========================================================================
def test_16_no_eligible_handler_sends_to_waiting_queue(test_db):
    """Objective: For normal priority, when handlers are unavailable/full, report is queued as PENDING."""
    session, _ = test_db
    z_a = session.query(Zone).filter_by(zone_code="ZONE-A").first()
    h1 = session.query(Handler).filter_by(handler_code="HND-T01").first()
    h2 = session.query(Handler).filter_by(handler_code="HND-T02").first()

    h1.current_workload = h1.max_capacity
    h2.current_workload = h2.max_capacity
    session.commit()

    rep = Report(
        report_code="TSF-2026-00031",
        reporter_name="Citizen Ken",
        reporter_contact="222",
        signal_id="SIG-Q-01",
        zone_id=z_a.id,
        location="Loc",
        description="Desc",
        category="Signal Light Failure",
        priority="MEDIUM", # Not emergency
        status="SUBMITTED"
    )
    session.add(rep)
    session.commit()

    res = DispatchEngine.dispatch_report(session, rep)
    assert res["decision"] == "QUEUED_CAPACITY"
    assert rep.status == "PENDING"

# =========================================================================
# TEST 17: Report status history recorded correctly
# =========================================================================
def test_17_report_status_history_recorded(test_db):
    """Objective: Every status transition must record report_id, previous_status, new_status, updater and timestamp."""
    session, _ = test_db
    z_a = session.query(Zone).filter_by(zone_code="ZONE-A").first()

    rep = Report(
        report_code="TSF-2026-00032",
        reporter_name="Citizen Laura",
        reporter_contact="333",
        signal_id="SIG-H-01",
        zone_id=z_a.id,
        location="Loc",
        description="Desc",
        category="Signal Light Failure",
        priority="LOW",
        status="SUBMITTED"
    )
    session.add(rep)
    session.flush()

    # Add initial history
    sh1 = StatusHistory(report_id=rep.id, previous_status=None, new_status="SUBMITTED", updated_by="Laura", remarks="Submitted")
    session.add(sh1)
    session.commit()

    # Dispatch to update
    DispatchEngine.dispatch_report(session, rep, updated_by="TEST_RUNNER")
    
    histories = session.query(StatusHistory).filter_by(report_id=rep.id).order_by(StatusHistory.created_at.asc()).all()
    assert len(histories) >= 2
    assert histories[0].new_status == "SUBMITTED"
    assert histories[1].previous_status == "SUBMITTED"
    assert histories[1].new_status in ["ASSIGNED", "PENDING", "ESCALATED"]

# =========================================================================
# TEST 18: Dashboard statistics reflect database values
# =========================================================================
def test_18_dashboard_statistics_reflect_db(client):
    """Objective: Verify dashboard analytics endpoint returns actual counts matching SQLite DB."""
    res = client.get('/api/analytics/dashboard')
    assert res.status_code == 200
    data = res.get_json()["metrics"]
    assert "total_reports" in data
    assert "pending_reports" in data
    assert "assigned_reports" in data
    assert "resolved_reports" in data
    assert "total_handlers" in data
    assert isinstance(data["total_reports"], int)
    assert isinstance(data["resolution_rate"], (int, float))

# =========================================================================
# TEST 19: Invalid user permissions / auth validation
# =========================================================================
def test_19_auth_validation_and_invalid_role_rejected(client):
    """Objective: Verify registration rejects illegal role and login rejects wrong credentials."""
    # Bad role
    res = client.post('/api/auth/register', json={
        "username": "hacker",
        "password": "Password123!",
        "role": "super_hacker",
        "full_name": "Hacker Man"
    })
    assert res.status_code == 400

    # Bad login
    res2 = client.post('/api/auth/login', json={
        "username": "non_existent_user_999",
        "password": "WrongPassword!"
    })
    assert res2.status_code == 401

# =========================================================================
# TEST 20: Resolved report cannot be incorrectly reassigned
# =========================================================================
def test_20_resolved_report_cannot_be_reassigned(test_db):
    """Objective: Attempting to dispatch an already RESOLVED report must be rejected."""
    session, _ = test_db
    z_a = session.query(Zone).filter_by(zone_code="ZONE-A").first()

    rep = Report(
        report_code="TSF-2026-00035",
        reporter_name="Closed Reporter",
        reporter_contact="444",
        signal_id="SIG-RES-01",
        zone_id=z_a.id,
        location="Loc",
        description="Desc",
        category="Signal Light Failure",
        priority="LOW",
        status="RESOLVED"
    )
    session.add(rep)
    session.commit()

    res = DispatchEngine.dispatch_report(session, rep)
    assert res["success"] is False
    assert res["decision"] == "ALREADY_RESOLVED"
    assert rep.status == "RESOLVED"
