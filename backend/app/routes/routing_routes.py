from flask import Blueprint, request, jsonify
from app.services.db_session import get_session
from app.models.schema import RoutingRule, Zone, Handler
from config import Config

routing_bp = Blueprint('routing_bp', __name__, url_prefix='/api/routing')

@routing_bp.route('/rules', methods=['GET'])
def get_rules():
    db = get_session()
    try:
        rules = db.query(RoutingRule).all()
        return jsonify({
            "count": len(rules),
            "rules": [r.to_dict() for r in rules]
        }), 200
    finally:
        db.close()

@routing_bp.route('/rules', methods=['POST'])
def create_rule():
    data = request.get_json() or {}
    zone_id = data.get('zone_id')
    category = data.get('category')
    primary_handler_id = data.get('primary_handler_id')
    backup_handler_id = data.get('backup_handler_id')
    escalation_path = data.get('escalation_path', 'SUPERVISOR_RAPID_ESCALATION')

    if not zone_id or not category or not primary_handler_id:
        return jsonify({"error": "zone_id, category, and primary_handler_id are required."}), 400

    if category not in Config.FAULT_CATEGORIES:
        return jsonify({"error": f"Invalid category. Must be one of: {Config.FAULT_CATEGORIES}"}), 400

    db = get_session()
    try:
        existing = db.query(RoutingRule).filter_by(zone_id=zone_id, category=category).first()
        if existing:
            return jsonify({"error": "Routing rule for this Zone and Category already exists."}), 409

        rule = RoutingRule(
            zone_id=zone_id,
            category=category,
            primary_handler_id=primary_handler_id,
            backup_handler_id=backup_handler_id,
            escalation_path=escalation_path,
            is_active=True
        )
        db.add(rule)
        db.commit()
        return jsonify({"message": "Routing rule created.", "rule": rule.to_dict()}), 201
    finally:
        db.close()

@routing_bp.route('/rules/<int:rule_id>', methods=['PUT'])
def update_rule(rule_id):
    data = request.get_json() or {}
    db = get_session()
    try:
        rule = db.query(RoutingRule).filter_by(id=rule_id).first()
        if not rule:
            return jsonify({"error": f"Routing rule {rule_id} not found"}), 404

        if 'primary_handler_id' in data:
            rule.primary_handler_id = data['primary_handler_id']
        if 'backup_handler_id' in data:
            rule.backup_handler_id = data['backup_handler_id']
        if 'escalation_path' in data:
            rule.escalation_path = data['escalation_path']
        if 'is_active' in data:
            rule.is_active = bool(data['is_active'])

        db.commit()
        return jsonify({"message": "Routing rule updated.", "rule": rule.to_dict()}), 200
    finally:
        db.close()

@routing_bp.route('/zones', methods=['GET'])
def get_zones():
    db = get_session()
    try:
        zones = db.query(Zone).all()
        return jsonify({
            "count": len(zones),
            "zones": [z.to_dict() for z in zones]
        }), 200
    finally:
        db.close()

@routing_bp.route('/zones', methods=['POST'])
def create_zone():
    data = request.get_json() or {}
    zone_code = data.get('zone_code', '').strip().upper()
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()

    if not zone_code or not name:
        return jsonify({"error": "zone_code and name are required."}), 400

    db = get_session()
    try:
        existing = db.query(Zone).filter_by(zone_code=zone_code).first()
        if existing:
            return jsonify({"error": f"Zone '{zone_code}' already exists."}), 409

        z = Zone(zone_code=zone_code, name=name, description=description, is_active=True)
        db.add(z)
        db.commit()
        return jsonify({"message": "Zone created.", "zone": z.to_dict()}), 201
    finally:
        db.close()
