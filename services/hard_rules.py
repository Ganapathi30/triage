import json
import re


def load_rules(path="data/rules.json"):
    with open(path, "r") as f:
        return json.load(f)


def _parse_duration_days(duration):
    if not duration:
        return None
    match = re.search(r"(\d+)", str(duration))
    if not match:
        return None
    return int(match.group(1))


def check_rules(data, age=None):
    rules = load_rules()

    symptoms = [s.lower() for s in data.get("symptoms", [])]
    severity = (data.get("severity") or "").lower()
    duration_days = _parse_duration_days(data.get("duration"))
    symptom_count = len(symptoms)

    for rule in rules:
        conditions = rule.get("conditions", {})

        if "symptoms_any" in conditions:
            if not any(s in symptoms for s in conditions["symptoms_any"]):
                continue

        if "symptoms_all" in conditions:
            if not all(s in symptoms for s in conditions["symptoms_all"]):
                continue

        if "severity" in conditions:
            if severity != conditions["severity"]:
                continue

        if "age_gt" in conditions:
            if age is None or age <= conditions["age_gt"]:
                continue

        if "duration_days_gt" in conditions:
            if duration_days is None or duration_days <= conditions["duration_days_gt"]:
                continue

        if "symptoms_count_gte" in conditions:
            if symptom_count < conditions["symptoms_count_gte"]:
                continue

        if "symptoms_count_lte" in conditions:
            if symptom_count > conditions["symptoms_count_lte"]:
                continue

        urgency = rule["urgency"]
        if urgency == "HIGH":
            urgency = "High Urgency (Immediate escalation)"
        elif urgency == "MEDIUM":
            urgency = "Medium Urgency (Prompt attention)"
        elif urgency == "LOW":
            urgency = "Low Urgency (Routine)"

        return {
            "urgency": urgency,
            "symptoms": data.get("symptoms", []),
            "reason": rule.get("reason"),
        }

    return None