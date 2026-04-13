import json

def load_rules(path="data/rules.json"):
    with open(path, "r") as f:
        return json.load(f)


def check_rules(data):
    rules = load_rules()

    symptoms = data.get("symptoms", [])
    severity = (data.get("severity") or "").lower()

    for rule in rules:
        
        if "symptoms_any" in rule:
            if not any(s in symptoms for s in rule["symptoms_any"]):
                continue

        if "severity" in rule:
            if severity != rule["severity"]:
                continue

        return {
            "urgency": rule["urgency"],
            "symptoms": rule["symptoms"],
        }

    return None