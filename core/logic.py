def is_enough_info(state):
    return (
        len(state["symptoms"]) > 0 and
        state["duration"] is not None and
        state["severity"] is not None
    )


def get_followup_question(state):
    if not state["symptoms"]:
        return "What symptoms is the patient experiencing?"

    if not state["duration"]:
        return "How long have these symptoms been present?"

    if not state["severity"]:
        return "How severe are the symptoms? (Mild, Moderate, Severe)"

    return None