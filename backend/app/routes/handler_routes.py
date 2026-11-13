from datetime import datetime
from flask import Blueprint, request, jsonify
from app.services.db_session import get_session
from app.models.schema import Handler, Assignment, Report, StatusHistory

handler_bp = Blueprint('handler_bp', __name__, url_prefix='/api/handlers')

@handler_bp.route('', methods=['GET'])
def list_handlers():
    db = get_session()
    try:
        handlers = db.query(Handler).all()
        return jsonify({
            "count": len(handlers),
            "handlers": [h.to_dict() for h in handlers]
        }), 200
    finally:
        db.close()

@handler_bp.route('/<int:handler_id>', methods=['GET'])
def get_handler(handler_id):
    db = get_session()
    try:
        handler = db.query(Handler).filter_by(id=handler_id).first()
        if not handler:
            return jsonify({"error": f"Handler {handler_id} not found"}), 404

        active_assignments = db.query(Assignment).filter_by(
            handler_id=handler.id,
            status="ACTIVE"
        ).all()

        res = handler.to_dict()
        res["active_assignments"] = [a.to_dict() for a in active_assignments]
        return jsonify(res), 200
    finally:
        db.close()

@handler_bp.route('/<int:handler_id>/availability', methods=['PUT'])
def update_availability(handler_id):
    data = request.get_json() or {}
    db = get_session()
    try:
        handler = db.query(Handler).filter_by(id=handler_id).first()
        if not handler:
            return jsonify({"error": f"Handler {handler_id} not found"}), 404

        is_avail = data.get('is_available')
        if is_avail is not None:
            handler.is_available = bool(is_avail)
            db.commit()

        return jsonify({
            "message": f"Handler {handler.name} availability updated to {handler.is_available}.",
            "handler": handler.to_dict()
        }), 200
    finally:
        db.close()

@handler_bp.route('/<int:handler_id>/capacity', methods=['PUT'])
def update_capacity(handler_id):
    data = request.get_json() or {}
    db = get_session()
    try:
        handler = db.query(Handler).filter_by(id=handler_id).first()
        if not handler:
            return jsonify({"error": f"Handler {handler_id} not found"}), 404

        max_cap = data.get('max_capacity')
        if max_cap is not None:
            val = int(max_cap)
            if val < 1:
                return jsonify({"error": "Capacity must be at least 1."}), 400
            handler.max_capacity = val
            db.commit()

        return jsonify({
            "message": f"Handler {handler.name} capacity updated to {handler.max_capacity}.",
            "handler": handler.to_dict()
        }), 200
    finally:
        db.close()

@handler_bp.route('/<int:handler_id>/assignments', methods=['GET'])
def get_handler_assignments(handler_id):
    status_filter = request.args.get('status')
    db = get_session()
    try:
        handler = db.query(Handler).filter_by(id=handler_id).first()
        if not handler:
            return jsonify({"error": f"Handler {handler_id} not found"}), 404

        query = db.query(Assignment).filter_by(handler_id=handler.id)
        if status_filter:
            query = query.filter_by(status=status_filter.upper())

        assignments = query.order_by(Assignment.assigned_at.desc()).all()
        results = []
        for a in assignments:
            item = a.to_dict()
            item["report_details"] = a.report.to_dict() if a.report else None
            results.append(item)

        return jsonify({
            "handler": handler.to_dict(),
            "count": len(results),
            "assignments": results
        }), 200
    finally:
        db.close()

@handler_bp.route('/assignments/<int:assignment_id>/status', methods=['POST'])
def update_assignment_status(assignment_id):
    data = request.get_json() or {}
    new_status = data.get('status', '').upper()
    notes = data.get('resolution_notes', '')
    updated_by = data.get('updated_by', 'HANDLER')

    if not new_status:
        return jsonify({"error": "Status is required."}), 400

    db = get_session()
    try:
        assignment = db.query(Assignment).filter_by(id=assignment_id).first()
        if not assignment:
            return jsonify({"error": f"Assignment {assignment_id} not found"}), 404

        report = assignment.report
        handler = assignment.handler

        old_report_status = report.status if report else "UNKNOWN"

        if new_status == "IN_PROGRESS":
            if report:
                report.status = "IN_PROGRESS"
                report.updated_at = datetime.utcnow()
            assignment.status = "ACTIVE"
            if notes:
                assignment.resolution_notes = notes

            sh = StatusHistory(
                report_id=report.id,
                previous_status=old_report_status,
                new_status="IN_PROGRESS",
                updated_by=updated_by,
                remarks=notes or "Work begun by handler.",
                created_at=datetime.utcnow()
            )
            db.add(sh)

        elif new_status == "RESOLVED":
            if report:
                report.status = "RESOLVED"
                report.updated_at = datetime.utcnow()
            assignment.status = "COMPLETED"
            assignment.completed_at = datetime.utcnow()
            assignment.resolution_notes = notes or "Fault resolved."

            # Decrement handler workload
            if handler:
                handler.current_workload = max(0, handler.current_workload - 1)

            sh = StatusHistory(
                report_id=report.id,
                previous_status=old_report_status,
                new_status="RESOLVED",
                updated_by=updated_by,
                remarks=notes or "Fault marked resolved by technician.",
                created_at=datetime.utcnow()
            )
            db.add(sh)

        elif new_status == "REASSIGNED":
            assignment.status = "REASSIGNED"
            if handler:
                handler.current_workload = max(0, handler.current_workload - 1)

        db.commit()

        return jsonify({
            "message": f"Assignment updated to {new_status}.",
            "assignment": assignment.to_dict(),
            "report_status": report.status if report else None,
            "handler_workload": handler.current_workload if handler else None
        }), 200
    finally:
        db.close()
