from datetime import datetime
from flask import Blueprint, request, jsonify
from app.algorithms.dfa import ReportIdDFA
from app.services.db_session import get_session
from app.models.schema import Report

dfa_bp = Blueprint('dfa_bp', __name__, url_prefix='/api/dfa')

@dfa_bp.route('/simulate', methods=['POST'])
def simulate_dfa():
    data = request.get_json() or {}
    report_id = data.get('report_id', '')
    res = ReportIdDFA.simulate(report_id)
    return jsonify(res), 200

@dfa_bp.route('/info', methods=['GET'])
def get_dfa_info():
    return jsonify({
        "formal_definition": {
            "name": "Report Identifier Validation DFA",
            "states": ReportIdDFA.STATES,
            "alphabet": ["T", "S", "F", "-", "0-9"],
            "initial_state": ReportIdDFA.INITIAL_STATE,
            "accepting_states": list(ReportIdDFA.ACCEPTING_STATES),
            "trap_state": ReportIdDFA.TRAP_STATE,
            "pattern": "^TSF-[0-9]{4}-[0-9]{5}$",
            "state_descriptions": ReportIdDFA.get_state_descriptions()
        }
    }), 200

@dfa_bp.route('/generate-id', methods=['GET'])
def generate_report_id():
    db = get_session()
    try:
        current_year = datetime.utcnow().year
        # Count reports in current year
        prefix = f"TSF-{current_year}-"
        count = db.query(Report).filter(Report.report_code.like(f"{prefix}%")).count()
        next_seq = count + 1
        generated_id = f"{prefix}{next_seq:05d}"
        
        # Verify generated ID passes both DFA and Regex
        sim = ReportIdDFA.simulate(generated_id)
        return jsonify({
            "generated_id": generated_id,
            "dfa_valid": sim["is_accepted"],
            "regex_valid": sim["regex_match"],
            "equivalent": sim["equivalent"]
        }), 200
    finally:
        db.close()
