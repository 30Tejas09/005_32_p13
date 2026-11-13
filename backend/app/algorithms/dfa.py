import re

class ReportIdDFA:
    """
    Formal Deterministic Finite Automaton (DFA) for validating Traffic Signal Fault report identifiers.
    Format: TSF-YYYY-XXXXX (e.g. TSF-2026-00001)
    
    Formal 5-Tuple Definition:
      M = (Q, Sigma, delta, q0, F)
      Q: {q0, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11, q12, q13, q14, q_trap}
      Sigma: {'T', 'S', 'F', '-', '0'..'9'}
      q0: Initial state (expecting 'T')
      F: {q14} (Accepting state reached after 14 valid transitions)
      delta: Transition function
    """

    STATES = [
        "q0", "q1", "q2", "q3", "q4", "q5", "q6", "q7",
        "q8", "q9", "q10", "q11", "q12", "q13", "q14", "q_trap"
    ]
    
    INITIAL_STATE = "q0"
    ACCEPTING_STATES = {"q14"}
    TRAP_STATE = "q_trap"
    
    DIGITS = set("0123456789")
    EQUIVALENT_REGEX = r"^TSF-[0-9]{4}-[0-9]{5}$"

    @classmethod
    def get_state_descriptions(cls):
        return {
            "q0": "Start: Expecting 'T'",
            "q1": "Saw 'T': Expecting 'S'",
            "q2": "Saw 'S': Expecting 'F'",
            "q3": "Saw 'F': Expecting hyphen '-'",
            "q4": "Saw '-': Expecting Year digit 1",
            "q5": "Saw Year digit 1: Expecting Year digit 2",
            "q6": "Saw Year digit 2: Expecting Year digit 3",
            "q7": "Saw Year digit 3: Expecting Year digit 4",
            "q8": "Saw 4-digit Year: Expecting hyphen '-'",
            "q9": "Saw second '-': Expecting Sequence digit 1",
            "q10": "Saw Sequence digit 1: Expecting Sequence digit 2",
            "q11": "Saw Sequence digit 2: Expecting Sequence digit 3",
            "q12": "Saw Sequence digit 3: Expecting Sequence digit 4",
            "q13": "Saw Sequence digit 4: Expecting Sequence digit 5",
            "q14": "Accepting State: Valid TSF ID (14 chars)",
            "q_trap": "Rejection/Trap State: Malformed format"
        }

    @classmethod
    def transition(cls, current_state: str, char: str) -> tuple[str, str]:
        """
        Transition function delta(current_state, char) -> (next_state, reason)
        """
        if current_state == "q_trap":
            return "q_trap", "Remaining in trap state (already rejected)"

        if current_state == "q0":
            if char == 'T':
                return "q1", "Matched prefix 'T'"
            return "q_trap", f"Position 0: expected 'T', received '{char}'"

        if current_state == "q1":
            if char == 'S':
                return "q2", "Matched prefix 'S'"
            return "q_trap", f"Position 1: expected 'S', received '{char}'"

        if current_state == "q2":
            if char == 'F':
                return "q3", "Matched prefix 'F'"
            return "q_trap", f"Position 2: expected 'F', received '{char}'"

        if current_state == "q3":
            if char == '-':
                return "q4", "Matched first delimiter '-'"
            return "q_trap", f"Position 3: expected '-', received '{char}'"

        if current_state in ("q4", "q5", "q6", "q7"):
            step_idx = int(current_state[1:])
            year_digit_num = step_idx - 3
            if char in cls.DIGITS:
                next_st = f"q{step_idx + 1}"
                return next_st, f"Matched Year digit {year_digit_num} ('{char}')"
            return "q_trap", f"Position {step_idx}: expected Year digit (0-9), received '{char}'"

        if current_state == "q8":
            if char == '-':
                return "q9", "Matched second delimiter '-'"
            return "q_trap", f"Position 8: expected '-', received '{char}'"

        if current_state in ("q9", "q10", "q11", "q12", "q13"):
            step_idx = int(current_state[1:])
            seq_digit_num = step_idx - 8
            if char in cls.DIGITS:
                next_st = f"q{step_idx + 1}"
                return next_st, f"Matched Sequence digit {seq_digit_num} ('{char}')"
            return "q_trap", f"Position {step_idx}: expected Sequence digit (0-9), received '{char}'"

        if current_state == "q14":
            return "q_trap", f"String too long: unexpected extra character '{char}' beyond 14 characters"

        return "q_trap", f"Unexpected transition from state {current_state} on input '{char}'"

    @classmethod
    def simulate(cls, report_id: str) -> dict:
        """
        Simulate the DFA on the input string and return the step-by-step trace.
        """
        if report_id is None:
            return {
                "input": None,
                "is_valid": False,
                "current_state": "q_trap",
                "is_accepted": False,
                "steps": [],
                "error_reason": "Report identifier cannot be null",
                "regex_match": False,
                "equivalent": True
            }

        steps = []
        current_state = cls.INITIAL_STATE

        for idx, char in enumerate(report_id):
            source_state = current_state
            next_state, explanation = cls.transition(current_state, char)
            steps.append({
                "step": idx + 1,
                "char": char,
                "from_state": source_state,
                "to_state": next_state,
                "explanation": explanation
            })
            current_state = next_state
            if current_state == cls.TRAP_STATE:
                break

        is_accepted = (current_state in cls.ACCEPTING_STATES) and (len(report_id) == 14)
        error_reason = None
        if not is_accepted:
            if current_state == cls.TRAP_STATE:
                error_reason = steps[-1]["explanation"] if steps else "Invalid character transition"
            elif len(report_id) < 14:
                error_reason = f"Incomplete report identifier (length {len(report_id)}, expected 14). Reached non-accepting state {current_state}."
            else:
                error_reason = f"Final state {current_state} is not in accepting states {list(cls.ACCEPTING_STATES)}."

        # Evaluate Regex
        regex_match = bool(re.match(cls.EQUIVALENT_REGEX, report_id))
        is_equivalent = (is_accepted == regex_match)

        return {
            "input": report_id,
            "length": len(report_id),
            "final_state": current_state,
            "is_accepted": is_accepted,
            "is_valid": is_accepted,
            "steps": steps,
            "error_reason": error_reason,
            "regex_pattern": cls.EQUIVALENT_REGEX,
            "regex_match": regex_match,
            "equivalent": is_equivalent,
            "states_metadata": cls.get_state_descriptions()
        }

    @classmethod
    def validate(cls, report_id: str) -> tuple[bool, str]:
        res = cls.simulate(report_id)
        return res["is_accepted"], res["error_reason"] or "Valid TSF Identifier"
