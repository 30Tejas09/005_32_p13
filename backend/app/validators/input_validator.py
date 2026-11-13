import re
from app.algorithms.dfa import ReportIdDFA
from config import Config

class InputValidator:
    PHONE_REGEX = r'^\+?[0-9\s\-\(\)]{7,20}$'
    SIGNAL_ID_REGEX = r'^[A-Za-z0-9\-_]{3,32}$'

    @classmethod
    def validate_report_submission(cls, data: dict, existing_reports=None) -> dict:
        """
        Validates all fields of a report submission according to academic guidelines.
        Returns a dictionary with 'is_valid': bool, 'errors': dict, and 'dfa_result': dict.
        """
        errors = {}
        
        # 1. Required fields
        required_fields = [
            'reporter_name', 'reporter_contact', 'report_code',
            'signal_id', 'zone', 'location', 'description'
        ]
        for field in required_fields:
            val = data.get(field)
            if val is None or (isinstance(val, str) and not val.strip()):
                errors[field] = f"Field '{field}' is required and cannot be empty."

        # 2. Report Identifier DFA & Regex Validation
        report_code = data.get('report_code', '').strip() if data.get('report_code') else ''
        if not report_code:
            errors['report_code'] = "Report code is required."
            dfa_result = None
        else:
            dfa_result = ReportIdDFA.simulate(report_code)
            if not dfa_result['is_accepted']:
                errors['report_code'] = f"Malformed Report ID: {dfa_result['error_reason']}"
            if not dfa_result['equivalent']:
                errors['validation_integrity'] = "DFA and Regex validation parity error."

        # 3. Reporter contact number validation
        contact = str(data.get('reporter_contact', '')).strip()
        if contact and not re.match(cls.PHONE_REGEX, contact):
            errors['reporter_contact'] = "Invalid contact number format. Must contain 7-20 digits."

        # 4. Traffic Signal ID format
        sig_id = str(data.get('signal_id', '')).strip()
        if sig_id and not re.match(cls.SIGNAL_ID_REGEX, sig_id):
            errors['signal_id'] = "Invalid traffic signal ID format (letters, digits, dashes, 3-32 chars)."

        # 5. Priority validation (if provided)
        priority = data.get('priority', 'MEDIUM')
        if priority and priority.upper() not in Config.PRIORITIES:
            errors['priority'] = f"Invalid priority '{priority}'. Allowed: {list(Config.PRIORITIES.keys())}"

        # 6. Fault Description length
        desc = data.get('description', '')
        if desc and len(desc.strip()) < 5:
            errors['description'] = "Fault description must be at least 5 characters long."

        # 7. Duplicate submission check (same active report code or identical signal_id + active status)
        if existing_reports and report_code:
            for rep in existing_reports:
                if rep.report_code == report_code:
                    errors['report_code'] = f"Duplicate report identifier: '{report_code}' already exists in database."
                    break

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "dfa_result": dfa_result
        }
