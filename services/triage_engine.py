from services.hard_rules import check_rules
from services.scoring_engine import calculate_score, score_to_urgency


def hybrid_triage(data, age):
    # -------------------------
    # STEP 1: HARD RULES
    # -------------------------
    hard_result = check_rules(data)
    if hard_result:
        return hard_result

    # -------------------------
    # STEP 2: SCORING
    # -------------------------
    score = calculate_score(data, age)
    urgency = score_to_urgency(score)

    return {
        "urgency": urgency,
        "symptoms": data.get("symptoms"),
    }