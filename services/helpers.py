import re
import time
import uuid

import streamlit as st

from core.state import init_state


def build_extraction_prompt(user_input):
    return (
        "Extract symptoms, duration, and severity from the user input.\n"
        "Return ONLY valid JSON for this schema:\n"
        "{\n"
        "  \"symptoms\": [\"...\"],\n"
        "  \"duration\": \"...\" or null,\n"
        "  \"severity\": \"Mild|Moderate|Severe\" or null\n"
        "}\n"
        "Do not add any other text.\n\n"
        f"User input: {user_input}"
    )


def sanitize_extraction(user_input, data):
    if not isinstance(data, dict):
        return data
    if not re.search(r"\b(mild|moderate|severe)\b", user_input, re.IGNORECASE):
        data["severity"] = None
    return data


def new_session():
    session_id = str(uuid.uuid4())[:8]
    session = {
        "id": session_id,
        "patient_id": "",
        "age": None,
        "gender": "",
        "pending_patient_field": None,
        "state": init_state(),
        "messages": [],
    }
    return session


def ensure_sessions():
    if "sessions" not in st.session_state:
        st.session_state.sessions = [new_session()]
        st.session_state.active_session_id = st.session_state.sessions[0]["id"]


def get_active_session():
    for session in st.session_state.sessions:
        if session["id"] == st.session_state.active_session_id:
            return session
    session = new_session()
    st.session_state.sessions.append(session)
    st.session_state.active_session_id = session["id"]
    return session


def render_sidebar():
    st.sidebar.title("Sessions")

    if st.sidebar.button("+ New session"):
        session = new_session()
        st.session_state.sessions.append(session)
        st.session_state.active_session_id = session["id"]

    session_labels = {
        session["id"]: session["patient_id"] or f"Session {index + 1}"
        for index, session in enumerate(st.session_state.sessions)
    }

    selected = st.sidebar.radio(
        "Select session",
        options=[session["id"] for session in st.session_state.sessions],
        format_func=lambda session_id: session_labels.get(session_id, session_id),
    )
    st.session_state.active_session_id = selected


def next_patient_field(session):
    if not session.get("patient_id"):
        return "patient_id"
    if session.get("age") is None:
        return "age"
    if not session.get("gender"):
        return "gender"
    return None


def patient_prompt(field):
    if field == "patient_id":
        return "Please provide the patient ID."
    if field == "age":
        return "Please provide the patient's age."
    if field == "gender":
        return "Please provide the patient's gender."
    return None


def enqueue_symptom_prompt(session):
    prompt = "What symptoms is the patient experiencing?"
    session["messages"].append({"role": "assistant", "content": prompt})
    with st.chat_message("assistant"):
        st.write_stream(stream_text(prompt))


def suggested_action_for_urgency(urgency):
    urgency_text = str(urgency).lower()
    if "high" in urgency_text:
        return "Seek immediate medical attention. Contact emergency services or the nearest hospital."
    if "medium" in urgency_text:
        return "Seek medical attention within few hours or the next few days. Contact a clinic or urgent care for guidance."
    return "Monitor symptoms and consider scheduling a routine checkup."


def stream_text(text, delay=0.01):
    for char in text:
        yield char
        if delay:
            time.sleep(delay)
