import re
from config import Config

class FaultClassifier:
    """
    Five-Category Fault Classification Engine with deterministic conflict resolution
    and priority detection.
    """

    CATEGORIES = Config.FAULT_CATEGORIES
    
    # Priority ranking for conflict resolution (Lower index = higher priority when scores tie)
    CONFLICT_PRIORITY_ORDER = [
        "Signal Light Failure",
        "Controller / Electrical Failure",
        "Signal Timing Failure",
        "Sensor / Detection Failure",
        "Communication / Network Failure"
    ]

    # Keyword patterns and associated weights
    CATEGORY_RULES = {
        "Signal Light Failure": [
            (r"\b(red|yellow|green|amber)\b.*\b(light|lamp|bulb|aspect|head|signal)\b", 3),
            (r"\b(bulb|lamp|led|aspect)\b.*\b(burnt|out|broken|dead|damaged|smashed)\b", 3),
            (r"\b(all lights|all signals|entire signal|completely dark|all off|switched off|blackout)\b", 4),
            (r"\b(light|lamp|bulb)\s*(failure|not working|not turning on|blinking red|flashing red|dark)\b", 3),
            (r"\b(red light|yellow light|green light)\b", 2),
            (r"\b(no light|dark signal|dark lamp|dim light)\b", 3)
        ],
        "Signal Timing Failure": [
            (r"\b(timing|duration|interval|cycle|phase)\b.*\b(incorrect|wrong|too short|too long|stuck|frozen)\b", 3),
            (r"\b(timer|time clock|clock)\b.*\b(malfunction|drift|error|fault)\b", 3),
            (r"\b(unexpected|rapid|erratic|frequent)\b.*\b(switching|change|cycling)\b", 3),
            (r"\b(synchronization|sync|coordination|green wave)\b.*\b(issue|lost|fail|failure)\b", 3),
            (r"\b(phase skipped|pedestrian phase stuck|cycle length|offset error)\b", 3),
            (r"\b(timing failure|timing issue|stuck on green|stuck on red)\b", 3)
        ],
        "Controller / Electrical Failure": [
            (r"\b(controller|cabinet|microcontroller|logic unit)\b.*\b(malfunction|blown|fried|dead|rebooting)\b", 3),
            (r"\b(power|electrical|supply|grid|voltage|surge)\b.*\b(failure|loss|outage|drop|fluctuation)\b", 3),
            (r"\b(circuit|fuse|breaker|wiring|cable|ground fault)\b.*\b(tripped|burnt|short|broken)\b", 3),
            (r"\b(signal controller)\b.*\b(communication|error|fault|offline)\b", 3),
            (r"\b(power supply failure|electrical circuit fault|power outage)\b", 4)
        ],
        "Sensor / Detection Failure": [
            (r"\b(vehicle detection|sensor|detector)\b.*\b(malfunction|dead|broken|failing|error)\b", 3),
            (r"\b(inductive loop|loop detector|loop wire|in-pavement)\b.*\b(failure|cut|fault|broken)\b", 4),
            (r"\b(camera|video detection|optical sensor|cctv)\b.*\b(failure|foggy|offline|blind)\b", 3),
            (r"\b(pedestrian sensor|push button|crosswalk button|walk button)\b.*\b(failure|stuck|unresponsive)\b", 3),
            (r"\b(radar|microwave detector|traffic sensor)\b", 2)
        ],
        "Communication / Network Failure": [
            (r"\b(signal communication|telemetry|modem|router|switch)\b.*\b(failure|loss|offline|down)\b", 3),
            (r"\b(network|ethernet|cellular|4g|5g|ip connection)\b.*\b(connectivity|unreachable|loss|drop)\b", 3),
            (r"\b(central server|traffic control center|scada|atcs)\b.*\b(communication|link|disconnected)\b", 3),
            (r"\b(remote monitoring|remote access|management portal)\b.*\b(failure|unavailable|offline)\b", 3),
            (r"\b(packet loss|fiber optic severed|connection timeout)\b", 3)
        ]
    }

    # Emergency and priority keywords
    PRIORITY_PATTERNS = {
        "EMERGENCY": [
            r"\b(emergency|immediate danger|collision risk|accident occurred|fatal|fire|smoke|high speed collision)\b",
            r"\b(all lights off|completely black|all dark|major highway)\b"
        ],
        "CRITICAL": [
            r"\b(critical|heavy traffic|major junction|blind intersection|arterial road|both directions green|conflicting greens)\b",
            r"\b(power supply failure|controller dead|stuck on green)\b"
        ],
        "HIGH": [
            r"\b(high|red light not working|loop cut|heavy delay|school zone|hospital route)\b"
        ],
        "LOW": [
            r"\b(minor|pedestrian button worn|slight delay|cosmetic|intermittent|dim light)\b"
        ]
    }

    @classmethod
    def classify(cls, text: str) -> dict:
        """
        Classifies fault description into exactly one of the five categories.
        Returns detailed scoring and conflict resolution audit metadata.
        """
        if not text:
            text = ""

        cleaned = text.lower().strip()
        category_scores = {cat: 0 for cat in cls.CATEGORIES}
        matched_rules = {cat: [] for cat in cls.CATEGORIES}

        # Evaluate rules for each category
        for category, rules in cls.CATEGORY_RULES.items():
            for pattern, weight in rules:
                matches = re.findall(pattern, cleaned, re.IGNORECASE)
                if matches:
                    category_scores[category] += weight * len(matches)
                    matched_rules[category].append({
                        "pattern": pattern,
                        "weight": weight,
                        "matches_count": len(matches)
                    })

        # Identify all categories that scored > 0
        candidates = [
            {
                "category": cat,
                "score": category_scores[cat],
                "rules_matched": matched_rules[cat]
            }
            for cat in cls.CATEGORIES if category_scores[cat] > 0
        ]

        # Deterministic Conflict Resolution:
        # 1. Sort by score descending
        # 2. Tie-break by CONFLICT_PRIORITY_ORDER index (lower index wins)
        if candidates:
            candidates.sort(
                key=lambda x: (
                    -x["score"],
                    cls.CONFLICT_PRIORITY_ORDER.index(x["category"])
                )
            )
            primary_candidate = candidates[0]
            detected_category = primary_candidate["category"]
            max_score = primary_candidate["score"]
            total_score = sum(c["score"] for c in candidates)
            confidence = round(max_score / total_score, 2) if total_score > 0 else 1.0

            if len(candidates) > 1:
                resolution_rule = f"Multi-category match ({len(candidates)} categories). Selected '{detected_category}' by highest score ({max_score}) and safety precedence rank {cls.CONFLICT_PRIORITY_ORDER.index(detected_category) + 1}."
            else:
                resolution_rule = f"Unanimous category match with score {max_score}."
        else:
            # Fallback default category (Safety first: Signal Light Failure)
            detected_category = cls.CONFLICT_PRIORITY_ORDER[0]
            confidence = 0.50
            resolution_rule = "DEFAULT_FALLBACK_RULE: No specific pattern matched. Assigned primary safety category 'Signal Light Failure' for inspection."

        # Detect recommended priority
        suggested_priority = cls.detect_priority(cleaned, detected_category)

        return {
            "primary_category": detected_category,
            "confidence_score": confidence,
            "resolution_rule": resolution_rule,
            "candidates": candidates,
            "all_scores": category_scores,
            "suggested_priority": suggested_priority
        }

    @classmethod
    def detect_priority(cls, text: str, category: str = None) -> str:
        """
        Determines the priority level based on text keywords and category severity.
        """
        cleaned = text.lower()
        for prio in ["EMERGENCY", "CRITICAL", "HIGH", "LOW"]:
            for pattern in cls.PRIORITY_PATTERNS[prio]:
                if re.search(pattern, cleaned, re.IGNORECASE):
                    return prio

        # Category-based default baseline if no explicit keyword found
        if category == "Signal Light Failure" and ("red" in cleaned or "dark" in cleaned or "blackout" in cleaned):
            return "HIGH"
        if category == "Controller / Electrical Failure":
            return "HIGH"
        if category == "Signal Timing Failure":
            return "MEDIUM"
        if category == "Sensor / Detection Failure":
            return "MEDIUM"
        if category == "Communication / Network Failure":
            return "LOW"

        return "MEDIUM"
