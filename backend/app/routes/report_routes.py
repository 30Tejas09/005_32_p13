from datetime import datetime
import json
from flask import Blueprint, request, jsonify, session
from app.services.db_session import get_session
from app.models.schema import (
    Report, Zone, Handler, Assignment, StatusHistory,
    DispatchLog, ClassificationLog
)
from app.validators.input_validator import InputValidator
from app.algorithms.classifier import FaultClassifier
from app.algorithms.dispatcher import DispatchEngine
from app.algorithms.dfa import ReportIdDFA
from config import Config

report_bp = Blueprint('report_bp', __name__, url_prefix='/api/reports')

@report_bp.route('/preview-classification', methods=['POST'])
def preview_classification():
    data = request.get_json() or {}
    text = data.get('description', '')
    res = FaultClassifier.classify(text)
    return jsonify(res), 200

@report_bp.route('/submit', methods=['POST'])
def submit_report():
    data = request.get_json() or {}
    db = get_session()
    try:
        # Step 1: Input Validation
        existing_reports = db.query(Report).all()
        validation_res = InputValidator.validate_report_submission(data, existing_reports)
        
        # If DFA or other input validation fails: Reject immediately before dispatch
        if not validation_res['is_valid']:
            return jsonify({
                "success": False,
                "status": "REJECTED",
                "error": "Validation Failed",
                "validation_errors": validation_res['errors'],
                "dfa_result": validation_res['dfa_result']
            }), 400

        # Step 2: Fault Classification
        description = data.get('description', '').strip()
        custom_category = data.get('category')
        classification_res = FaultClassifier.classify(description)
        
        # Use auto-detected category unless valid override provided
        if custom_category and custom_category in Config.FAULT_CATEGORIES:
            final_category = custom_category
            is_override = (custom_category != classification_res['primary_category'])
        else:
            final_category = classification_res['primary_category']
            is_override = False

        # Step 3: Priority Detection
        priority = data.get('priority', '').upper()
        if not priority or priority not in Config.PRIORITIES:
            priority = classification_res['suggested_priority']

        # Resolve Zone
        zone_str = str(data.get('zone', '')).strip()
        zone = db.query(Zone).filter(
            (Zone.zone_code == zone_str.upper()) | (Zone.name.ilike(f"%{zone_str}%"))
        ).first()

        reporter_name = data.get('reporter_name', '').strip()
        report_code = data.get('report_code', '').strip()

        # Create Report
        report = Report(
            report_code=report_code,
            reporter_name=reporter_name,
            reporter_contact=data.get('reporter_contact', '').strip(),
            signal_id=data.get('signal_id', '').strip(),
            zone_id=zone.id if zone else None,
            zone_raw=zone_str,
            location=data.get('location', '').strip(),
            description=description,
            category=final_category,
            priority=priority,
            status="SUBMITTED",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(report)
        db.flush()

        # Classification Log
        cl = ClassificationLog(
            report_id=report.id,
            detected_category=classification_res['primary_category'],
            matched_categories=json.dumps([c['category'] for c in classification_res['candidates']]),
            confidence_score=classification_res['confidence_score'],
            resolution_rule=classification_res['resolution_rule'],
            is_manual_override=is_override,
            overridden_by=reporter_name if is_override else None,
            original_category=classification_res['primary_category'] if is_override else None,
            timestamp=datetime.utcnow()
        )
        db.add(cl)

        # Initial Status History
        sh = StatusHistory(
            report_id=report.id,
            previous_status=None,
            new_status="SUBMITTED",
            updated_by=reporter_name,
            remarks="Report submitted and validated via DFA.",
            created_at=datetime.utcnow()
        )
        db.add(sh)
        db.commit()

        # Step 4-11: Dispatch Report immediately
        dispatch_res = DispatchEngine.dispatch_report(db, report, updated_by=reporter_name)

        return jsonify({
            "success": True,
            "message": "Report submitted and dispatched successfully.",
            "report": report.to_dict(),
            "dfa_validation": validation_res['dfa_result'],
            "classification": classification_res,
            "dispatch_decision": dispatch_res
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@report_bp.route('', methods=['GET'])
def list_reports():
    status = request.args.get('status')
    zone_code = request.args.get('zone')
    category = request.args.get('category')
    priority = request.args.get('priority')
    search_q = request.args.get('q')

    db = get_session()
    try:
        query = db.query(Report)
        if status:
            query = query.filter(Report.status == status.upper())
        if category:
            query = query.filter(Report.category == category)
        if priority:
            query = query.filter(Report.priority == priority.upper())
        if zone_code:
            query = query.join(Report.zone).filter(Zone.zone_code == zone_code.upper())
        if search_q:
            q_filter = f"%{search_q}%"
            query = query.filter(
                (Report.report_code.ilike(q_filter)) |
                (Report.signal_id.ilike(q_filter)) |
                (Report.location.ilike(q_filter)) |
                (Report.description.ilike(q_filter)) |
                (Report.reporter_name.ilike(q_filter))
            )

        reports = query.order_by(Report.created_at.desc()).all()
        return jsonify({
            "count": len(reports),
            "reports": [r.to_dict() for r in reports]
        }), 200
    finally:
        db.close()

@report_bp.route('/<id_or_code>', methods=['GET'])
def get_report(id_or_code):
    db = get_session()
    try:
        if str(id_or_code).isdigit():
            report = db.query(Report).filter_by(id=int(id_or_code)).first()
        else:
            report = db.query(Report).filter_by(report_code=id_or_code).first()

        if not report:
            return jsonify({"error": f"Report '{id_or_code}' not found."}), 404

        history = [h.to_dict() for h in report.status_history]
        dispatch_logs = [l.to_dict() for l in report.dispatch_logs]
        classification_logs = [c.to_dict() for c in report.classification_logs]
        assignments = [a.to_dict() for a in report.assignments]

        report_dict = report.to_dict()
        report_dict["history"] = history
        report_dict["dispatch_logs"] = dispatch_logs
        report_dict["classification_logs"] = classification_logs
        report_dict["all_assignments"] = assignments

        return jsonify(report_dict), 200
    finally:
        db.close()

@report_bp.route('/<id_or_code>', methods=['PUT'])
def update_report(id_or_code):
    data = request.get_json() or {}
    db = get_session()
    try:
        if str(id_or_code).isdigit():
            report = db.query(Report).filter_by(id=int(id_or_code)).first()
        else:
            report = db.query(Report).filter_by(report_code=id_or_code).first()

        if not report:
            return jsonify({"error": f"Report '{id_or_code}' not found."}), 404

        updated_by = data.get('updated_by', 'ADMIN')

        # Check for category manual correction (Admin override with audit trail)
        new_category = data.get('category')
        if new_category and new_category in Config.FAULT_CATEGORIES and new_category != report.category:
            orig_cat = report.category
            report.category = new_category

            cl = ClassificationLog(
                report_id=report.id,
                detected_category=new_category,
                matched_categories=json.dumps([new_category]),
                confidence_score=1.0,
                resolution_rule="Manual Admin Override",
                is_manual_override=True,
                overridden_by=updated_by,
                original_category=orig_cat,
                timestamp=datetime.utcnow()
            )
            db.add(cl)

            sh = StatusHistory(
                report_id=report.id,
                previous_status=report.status,
                new_status=report.status,
                updated_by=updated_by,
                remarks=f"Manual category correction: Changed from '{orig_cat}' to '{new_category}'.",
                created_at=datetime.utcnow()
            )
            db.add(sh)

        # Check for priority update
        new_priority = data.get('priority')
        if new_priority and new_priority.upper() in Config.PRIORITIES and new_priority.upper() != report.priority:
            report.priority = new_priority.upper()

        # Check for status update
        new_status = data.get('status')
        if new_status and new_status.upper() in Config.STATUSES and new_status.upper() != report.status:
            old_s = report.status
            report.status = new_status.upper()
            sh = StatusHistory(
                report_id=report.id,
                previous_status=old_s,
                new_status=report.status,
                updated_by=updated_by,
                remarks=data.get('remarks', f"Status updated to {report.status}."),
                created_at=datetime.utcnow()
            )
            db.add(sh)

        report.updated_at = datetime.utcnow()
        db.commit()

        return jsonify({
            "message": "Report updated successfully.",
            "report": report.to_dict()
        }), 200
    finally:
        db.close()

@report_bp.route('/<id_or_code>/history', methods=['GET'])
def get_report_history(id_or_code):
    db = get_session()
    try:
        if str(id_or_code).isdigit():
            report = db.query(Report).filter_by(id=int(id_or_code)).first()
        else:
            report = db.query(Report).filter_by(report_code=id_or_code).first()

        if not report:
            return jsonify({"error": "Report not found"}), 404

        history = [h.to_dict() for h in report.status_history]
        return jsonify({"history": history}), 200
    finally:
        db.close()
