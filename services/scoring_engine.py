def calculate_score(data, age):
    score = 0

    symptoms = data.get("symptoms", [])
    severity = (data.get("severity") or "").lower()
    duration = data.get("duration") or ""

    # -------------------------
    # SEVERITY
    # -------------------------
    if severity == "severe":
        score += 4
    elif severity == "moderate":
        score += 2
    elif severity == "mild":
        score += 0

    # -------------------------
    # MULTIPLE SYMPTOMS
    # -------------------------
    if len(symptoms) >= 3:
        score += 2

    # -------------------------
    # DURATION
    # -------------------------
    if "day" in duration:
        try:
            days = int(duration.split()[0])
            if days > 3:
                score += 2
        except:
            pass

    # -------------------------
    # AGE
    # -------------------------
    if age > 60:
        score += 2

    return score


def score_to_urgency(score):
    if score >= 7:
        return "HIGH"
    elif score >= 3:
        return "MEDIUM"
    else:
        return "LOW"