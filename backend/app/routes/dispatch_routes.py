from datetime import datetime
from flask import Blueprint, request, jsonify
from app.services.db_session import get_session
from app.models.schema import Report, DispatchLog, Assignment, StatusHistory
from app.algorithms.dispatcher import DispatchEngine

dispatch_bp = Blueprint('dispatch_bp', __name__, url_prefix='/api/dispatch')

@dispatch_bp.route('/dispatch-report/<int:report_id>', methods=['POST'])
def trigger_dispatch(report_id):
    db = get_session()
    try:
        report = db.query(Report).filter_by(id=report_id).first()
        if not report:
            return jsonify({"error": f"Report id {report_id} not found."}), 404

        data = request.get_json() or {}
        updated_by = data.get('updated_by', 'ADMIN_DISPATCHER')

        result = DispatchEngine.dispatch_report(db, report, updated_by=updated_by)
        return jsonify({
            "report_id": report.id,
            "report_code": report.report_code,
            "status": report.status,
            "dispatch_result": result
        }), 200
    finally:
        db.close()

@dispatch_bp.route('/waiting-queue', methods=['GET'])
def get_waiting_queue():
    db = get_session()
    try:
        queue = DispatchEngine.get_waiting_queue(db)
        return jsonify({
            "count": len(queue),
            "queue": [r.to_dict() for r in queue]
        }), 200
    finally:
        db.close()

@dispatch_bp.route('/escalate/<int:report_id>', methods=['POST'])
def force_escalate(report_id):
    data = request.get_json() or {}
    reason = data.get('reason', 'Manual emergency escalation triggered by administrator.')
    updated_by = data.get('updated_by', 'ADMIN')

    db = get_session()
    try:
        report = db.query(Report).filter_by(id=report_id).first()
        if not report:
            return jsonify({"error": f"Report id {report_id} not found."}), 404

        old_status = report.status
        report.status = "ESCALATED"

        # Check existing active assignment
        active_asg = db.query(Assignment).filter_by(report_id=report.id, status="ACTIVE").first()
        if active_asg:
            active_asg.status = "REASSIGNED"
            if active_asg.handler:
                active_asg.handler.current_workload = max(0, active_asg.handler.current_workload - 1)

        # Create escalation assignment
        new_asg = Assignment(
            report_id=report.id,
            handler_id=None,
            status="ACTIVE",
            assignment_type="ESCALATION",
            assigned_at=datetime.utcnow(),
            resolution_notes=f"Escalation note: {reason}"
        )
        db.add(new_asg)

        log = DispatchLog(
            report_id=report.id,
            decision="MANUAL_ESCALATION",
            reason=reason,
            primary_handler_id=None,
            assigned_handler_id=None,
            is_backup=False,
            is_escalated=True,
            is_queued=False,
            timestamp=datetime.utcnow()
        )
        db.add(log)

        sh = StatusHistory(
            report_id=report.id,
            previous_status=old_status,
            new_status="ESCALATED",
            updated_by=updated_by,
            remarks=reason,
            created_at=datetime.utcnow()
        )
        db.add(sh)
        db.commit()

        return jsonify({
            "message": "Report escalated successfully.",
            "report": report.to_dict()
        }), 200
    finally:
        db.close()

@dispatch_bp.route('/logs', methods=['GET'])
def get_dispatch_logs():
    limit = int(request.args.get('limit', 50))
    db = get_session()
    try:
        logs = db.query(DispatchLog).order_by(DispatchLog.timestamp.desc()).limit(limit).all()
        return jsonify({
            "count": len(logs),
            "logs": [l.to_dict() for l in logs]
        }), 200
    finally:
        db.close()
