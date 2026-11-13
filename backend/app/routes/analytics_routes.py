from flask import Blueprint, jsonify
from sqlalchemy import func
from app.services.db_session import get_session
from app.models.schema import Report, Handler, Zone, Assignment, StatusHistory
from config import Config

analytics_bp = Blueprint('analytics_bp', __name__, url_prefix='/api/analytics')

@analytics_bp.route('/dashboard', methods=['GET'])
def get_dashboard_metrics():
    db = get_session()
    try:
        total_reports = db.query(Report).count()
        pending = db.query(Report).filter_by(status='PENDING').count()
        assigned = db.query(Report).filter_by(status='ASSIGNED').count()
        in_progress = db.query(Report).filter_by(status='IN_PROGRESS').count()
        escalated = db.query(Report).filter_by(status='ESCALATED').count()
        resolved = db.query(Report).filter_by(status='RESOLVED').count()
        rejected = db.query(Report).filter_by(status='REJECTED').count()

        total_handlers = db.query(Handler).count()
        available_handlers = db.query(Handler).filter_by(is_available=True).count()
        total_capacity = db.query(func.sum(Handler.max_capacity)).scalar() or 0
        total_workload = db.query(func.sum(Handler.current_workload)).scalar() or 0

        resolution_rate = round((resolved / total_reports * 100), 1) if total_reports > 0 else 0.0

        return jsonify({
            "metrics": {
                "total_reports": total_reports,
                "pending_reports": pending,
                "assigned_reports": assigned,
                "in_progress_reports": in_progress,
                "escalated_reports": escalated,
                "resolved_reports": resolved,
                "rejected_reports": rejected,
                "resolution_rate": resolution_rate,
                "total_handlers": total_handlers,
                "available_handlers": available_handlers,
                "total_capacity": total_capacity,
                "total_workload": total_workload,
                "fleet_utilization": round((total_workload / total_capacity * 100), 1) if total_capacity > 0 else 0.0
            }
        }), 200
    finally:
        db.close()

@analytics_bp.route('/zone-distribution', methods=['GET'])
def get_zone_distribution():
    db = get_session()
    try:
        zones = db.query(Zone).all()
        data = []
        for z in zones:
            total = db.query(Report).filter_by(zone_id=z.id).count()
            resolved = db.query(Report).filter_by(zone_id=z.id, status='RESOLVED').count()
            active = total - resolved
            data.append({
                "zone_id": z.id,
                "zone_code": z.zone_code,
                "name": z.name,
                "total": total,
                "resolved": resolved,
                "active": active
            })
        return jsonify({"zone_distribution": data}), 200
    finally:
        db.close()

@analytics_bp.route('/category-distribution', methods=['GET'])
def get_category_distribution():
    db = get_session()
    try:
        total_reports = db.query(Report).count()
        data = []
        for cat in Config.FAULT_CATEGORIES:
            cnt = db.query(Report).filter_by(category=cat).count()
            pct = round((cnt / total_reports * 100), 1) if total_reports > 0 else 0.0
            data.append({
                "category": cat,
                "count": cnt,
                "percentage": pct
            })
        return jsonify({"category_distribution": data}), 200
    finally:
        db.close()

@analytics_bp.route('/priority-distribution', methods=['GET'])
def get_priority_distribution():
    db = get_session()
    try:
        data = []
        for prio in ["EMERGENCY", "CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            cnt = db.query(Report).filter_by(priority=prio).count()
            data.append({
                "priority": prio,
                "count": cnt,
                "rank": Config.PRIORITIES.get(prio)
            })
        return jsonify({"priority_distribution": data}), 200
    finally:
        db.close()

@analytics_bp.route('/handler-workload', methods=['GET'])
def get_handler_workload():
    db = get_session()
    try:
        handlers = db.query(Handler).all()
        data = []
        for h in handlers:
            utilization = round((h.current_workload / h.max_capacity * 100), 1) if h.max_capacity > 0 else 0.0
            data.append({
                "id": h.id,
                "handler_code": h.handler_code,
                "name": h.name,
                "zone": h.zone.zone_code if h.zone else "Global",
                "workload": h.current_workload,
                "capacity": h.max_capacity,
                "remaining": max(0, h.max_capacity - h.current_workload),
                "utilization_pct": utilization,
                "is_available": h.is_available
            })
        return jsonify({"handler_workload": data}), 200
    finally:
        db.close()

@analytics_bp.route('/recent-activity', methods=['GET'])
def get_recent_activity():
    db = get_session()
    try:
        history = db.query(StatusHistory).order_by(StatusHistory.created_at.desc()).limit(15).all()
        data = []
        for item in history:
            rep = item.report
            data.append({
                "id": item.id,
                "report_id": item.report_id,
                "report_code": rep.report_code if rep else "UNKNOWN",
                "previous_status": item.previous_status,
                "new_status": item.new_status,
                "updated_by": item.updated_by,
                "remarks": item.remarks,
                "timestamp": item.created_at.isoformat() if item.created_at else None
            })
        return jsonify({"recent_activity": data}), 200
    finally:
        db.close()
