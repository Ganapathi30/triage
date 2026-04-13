def init_state():
    return {
        "symptoms": [],
        "duration": None,
        "severity": None
    }


def update_state(state, new_data):
    if new_data.get("symptoms"):
        state["symptoms"] = list(set(state["symptoms"] + new_data["symptoms"]))

    if new_data.get("duration"):
        state["duration"] = new_data["duration"]

    if new_data.get("severity"):
        state["severity"] = new_data["severity"]

    return state