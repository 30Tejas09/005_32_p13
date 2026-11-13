from datetime import datetime
from config import Config
from app.models.schema import (
    Report, Handler, Zone, RoutingRule, Assignment,
    StatusHistory, DispatchLog, ClassificationLog
)

class DispatchEngine:
    """
    Traffic Signal Fault Dispatch Engine.
    Implements Zone-based Routing Table Lookup, Handler Availability, Capacity Constraints,
    Backup Handler Selection, Emergency Escalations, Waiting Queues, and Duplicate Prevention.
    """

    @classmethod
    def dispatch_report(cls, session, report: Report, updated_by: str = "SYSTEM_DISPATCHER") -> dict:
        """
        Executes the 11-step dispatch sequence with database transaction integrity.
        """
        # Step 0: Check if report is already resolved
        if report.status == "RESOLVED":
            return {
                "success": False,
                "decision": "ALREADY_RESOLVED",
                "reason": f"Report {report.report_code} is already resolved and cannot be reassigned.",
                "report_id": report.id
            }

        # Step 0b: Duplicate active assignment check
        existing_active = session.query(Assignment).filter_by(
            report_id=report.id,
            status="ACTIVE"
        ).first()
        if existing_active:
            return {
                "success": False,
                "decision": "DUPLICATE_ACTIVE_ASSIGNMENT_PREVENTED",
                "reason": f"Report {report.report_code} already has active handler assignment ({existing_active.handler.name if existing_active.handler else 'Escalated'}). Duplicate assignment prevented.",
                "report_id": report.id,
                "current_assignment": existing_active.to_dict()
            }

        # Step 4: Find matching zone
        zone = None
        if report.zone_id:
            zone = session.query(Zone).filter_by(id=report.zone_id, is_active=True).first()
        elif report.zone_raw:
            zone = session.query(Zone).filter(
                (Zone.zone_code == report.zone_raw.upper()) | 
                (Zone.name.ilike(f"%{report.zone_raw}%")),
                Zone.is_active == True
            ).first()

        # Edge Case A: UNKNOWN ZONE / UNRESOLVED ROUTING KEY
        if not zone:
            old_status = report.status
            report.status = "PENDING"
            
            log = DispatchLog(
                report_id=report.id,
                decision="FALLBACK_UNKNOWN_ZONE",
                reason=f"Unknown or unconfigured zone identifier '{report.zone_raw or 'NULL'}'. Routed to Central Fallback Correction Queue.",
                primary_handler_id=None,
                assigned_handler_id=None,
                is_backup=False,
                is_escalated=False,
                is_queued=True,
                timestamp=datetime.utcnow()
            )
            session.add(log)
            
            history = StatusHistory(
                report_id=report.id,
                previous_status=old_status,
                new_status="PENDING",
                updated_by=updated_by,
                remarks=f"Placed in Central Fallback Queue: Zone '{report.zone_raw}' unknown.",
                created_at=datetime.utcnow()
            )
            session.add(history)
            session.commit()

            return {
                "success": True,
                "decision": "FALLBACK_UNKNOWN_ZONE",
                "reason": f"Zone '{report.zone_raw}' not recognized. Report routed to Central Fallback Queue.",
                "assigned_handler": None,
                "status": "PENDING"
            }

        # Update report's resolved zone_id if needed
        report.zone_id = zone.id

        # Step 4b: Find routing table rule for (zone + category)
        routing_rule = session.query(RoutingRule).filter_by(
            zone_id=zone.id,
            category=report.category,
            is_active=True
        ).first()

        if not routing_rule:
            old_status = report.status
            report.status = "PENDING"
            log = DispatchLog(
                report_id=report.id,
                decision="NO_ROUTING_RULE",
                reason=f"No routing table rule configured for Zone '{zone.zone_code}' and category '{report.category}'. Placed in Waiting Queue.",
                primary_handler_id=None,
                assigned_handler_id=None,
                is_backup=False,
                is_escalated=False,
                is_queued=True,
                timestamp=datetime.utcnow()
            )
            session.add(log)
            session.commit()
            return {
                "success": False,
                "decision": "NO_ROUTING_RULE",
                "reason": f"No active routing rule for {zone.zone_code} + {report.category}",
                "status": "PENDING"
            }

        # Step 5: Primary handler check
        primary = routing_rule.primary_handler
        is_primary_eligible = False
        primary_reject_reasons = []

        if not primary:
            primary_reject_reasons.append("No primary handler defined in rule")
        else:
            if not primary.is_available:
                primary_reject_reasons.append(f"Primary handler {primary.name} is UNAVAILABLE")
            if primary.current_workload >= primary.max_capacity:
                primary_reject_reasons.append(f"Primary handler {primary.name} capacity exceeded ({primary.current_workload}/{primary.max_capacity})")
            if not primary_reject_reasons:
                is_primary_eligible = True

        # Step 8: Assign to Primary Handler
        if is_primary_eligible:
            primary.current_workload += 1
            old_status = report.status
            report.status = "ASSIGNED"
            
            assignment = Assignment(
                report_id=report.id,
                handler_id=primary.id,
                status="ACTIVE",
                assignment_type="PRIMARY",
                assigned_at=datetime.utcnow()
            )
            session.add(assignment)
            
            log = DispatchLog(
                report_id=report.id,
                decision="ASSIGNED_PRIMARY",
                reason=f"Assigned to primary handler {primary.name} ({primary.handler_code}). Workload: {primary.current_workload}/{primary.max_capacity}.",
                primary_handler_id=primary.id,
                assigned_handler_id=primary.id,
                is_backup=False,
                is_escalated=False,
                is_queued=False,
                timestamp=datetime.utcnow()
            )
            session.add(log)

            history = StatusHistory(
                report_id=report.id,
                previous_status=old_status,
                new_status="ASSIGNED",
                updated_by=updated_by,
                remarks=f"Dispatched to primary handler {primary.name}.",
                created_at=datetime.utcnow()
            )
            session.add(history)
            session.commit()

            return {
                "success": True,
                "decision": "ASSIGNED_PRIMARY",
                "reason": f"Dispatched to primary handler {primary.name}",
                "assigned_handler": primary.to_dict(),
                "status": "ASSIGNED"
            }

        # Step 9: Primary unavailable or capacity exceeded -> Check eligible backup handlers
        backup = routing_rule.backup_handler
        is_backup_eligible = False
        backup_reject_reasons = []

        if not backup:
            backup_reject_reasons.append("No backup handler configured in routing rule")
        else:
            if not backup.is_backup_eligible:
                backup_reject_reasons.append(f"Backup handler {backup.name} is marked not eligible for backups")
            if not backup.is_available:
                backup_reject_reasons.append(f"Backup handler {backup.name} is UNAVAILABLE")
            if backup.current_workload >= backup.max_capacity:
                backup_reject_reasons.append(f"Backup handler {backup.name} capacity exceeded ({backup.current_workload}/{backup.max_capacity})")
            if not backup_reject_reasons:
                is_backup_eligible = True

        if is_backup_eligible:
            backup.current_workload += 1
            old_status = report.status
            report.status = "ASSIGNED"

            assignment = Assignment(
                report_id=report.id,
                handler_id=backup.id,
                status="ACTIVE",
                assignment_type="BACKUP",
                assigned_at=datetime.utcnow()
            )
            session.add(assignment)

            reasons_combined = "; ".join(primary_reject_reasons)
            log = DispatchLog(
                report_id=report.id,
                decision="ASSIGNED_BACKUP",
                reason=f"Primary unavailable ({reasons_combined}). Dispatched to backup handler {backup.name} ({backup.handler_code}). Workload: {backup.current_workload}/{backup.max_capacity}.",
                primary_handler_id=primary.id if primary else None,
                assigned_handler_id=backup.id,
                is_backup=True,
                is_escalated=False,
                is_queued=False,
                timestamp=datetime.utcnow()
            )
            session.add(log)

            history = StatusHistory(
                report_id=report.id,
                previous_status=old_status,
                new_status="ASSIGNED",
                updated_by=updated_by,
                remarks=f"Dispatched to backup handler {backup.name}. Primary bypass reason: {reasons_combined}",
                created_at=datetime.utcnow()
            )
            session.add(history)
            session.commit()

            return {
                "success": True,
                "decision": "ASSIGNED_BACKUP",
                "reason": f"Primary unavailable ({reasons_combined}). Dispatched to backup handler {backup.name}.",
                "assigned_handler": backup.to_dict(),
                "status": "ASSIGNED"
            }

        # Step 10: Neither primary nor backup available -> Special Edge Case E: Emergency Priority Escalation
        is_emergency = report.priority in ("EMERGENCY", "CRITICAL")
        all_reasons = primary_reject_reasons + backup_reject_reasons

        if is_emergency:
            old_status = report.status
            report.status = "ESCALATED"

            assignment = Assignment(
                report_id=report.id,
                handler_id=None,
                status="ACTIVE",
                assignment_type="ESCALATION",
                assigned_at=datetime.utcnow()
            )
            session.add(assignment)

            log = DispatchLog(
                report_id=report.id,
                decision="ESCALATED_EMERGENCY",
                reason=f"Emergency/Critical priority override: Handlers unavailable ({'; '.join(all_reasons)}). Escalated immediately via {routing_rule.escalation_path}.",
                primary_handler_id=primary.id if primary else None,
                assigned_handler_id=None,
                is_backup=False,
                is_escalated=True,
                is_queued=False,
                timestamp=datetime.utcnow()
            )
            session.add(log)

            history = StatusHistory(
                report_id=report.id,
                previous_status=old_status,
                new_status="ESCALATED",
                updated_by=updated_by,
                remarks=f"Immediate Emergency Escalation ({routing_rule.escalation_path}). Priority={report.priority}.",
                created_at=datetime.utcnow()
            )
            session.add(history)
            session.commit()

            return {
                "success": True,
                "decision": "ESCALATED_EMERGENCY",
                "reason": f"Emergency Priority Escalation triggered: Handlers unavailable. Escalated to {routing_rule.escalation_path}.",
                "assigned_handler": None,
                "status": "ESCALATED"
            }
        else:
            # Place in waiting queue
            old_status = report.status
            report.status = "PENDING"

            log = DispatchLog(
                report_id=report.id,
                decision="QUEUED_CAPACITY",
                reason=f"No eligible primary or backup handler available ({'; '.join(all_reasons)}). Placed in Waiting Queue.",
                primary_handler_id=primary.id if primary else None,
                assigned_handler_id=None,
                is_backup=False,
                is_escalated=False,
                is_queued=True,
                timestamp=datetime.utcnow()
            )
            session.add(log)

            history = StatusHistory(
                report_id=report.id,
                previous_status=old_status,
                new_status="PENDING",
                updated_by=updated_by,
                remarks=f"Waiting Queue: Primary and backup handlers at capacity or unavailable.",
                created_at=datetime.utcnow()
            )
            session.add(history)
            session.commit()

            return {
                "success": True,
                "decision": "QUEUED_CAPACITY",
                "reason": f"Placed in Waiting Queue: {'; '.join(all_reasons)}",
                "assigned_handler": None,
                "status": "PENDING"
            }

    @classmethod
    def get_waiting_queue(cls, session) -> list:
        """
        Special Edge Case F: Returns waiting reports ordered deterministically:
        1. Priority Rank (EMERGENCY=1, CRITICAL=2, HIGH=3, MEDIUM=4, LOW=5)
        2. Submission time (created_at ASC - earliest submission first)
        """
        pending_reports = session.query(Report).filter(
            Report.status.in_(["PENDING", "SUBMITTED", "ESCALATED"])
        ).all()

        def sort_key(rep):
            prio_rank = Config.PRIORITIES.get(rep.priority, 99)
            created_ts = rep.created_at.timestamp() if rep.created_at else 0
            return (prio_rank, created_ts)

        pending_reports.sort(key=sort_key)
        return pending_reports
