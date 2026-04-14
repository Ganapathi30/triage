import time
import uuid
import re

import streamlit as st

from agent.triage_agent import create_triage_agent
from agent.formatter_agent import create_formatter_agent, format_triage
from services.extractor import parse_llm_output
from services.triage_engine import hybrid_triage
from core.state import init_state, update_state
from core.logic import is_enough_info, get_followup_question


APP_TITLE = "Triage Agent"


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


@st.cache_resource
def get_agents():
    return create_triage_agent(), create_formatter_agent()


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


st.set_page_config(page_title=APP_TITLE, layout="wide")
ensure_sessions()
render_sidebar()
active_session = get_active_session()
st.session_state.setdefault("busy", False)
st.session_state.setdefault("pending_user_input", None)

st.title(APP_TITLE)

triage_agent, formatter_agent = get_agents()

for message in active_session["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

pending_field = active_session.get("pending_patient_field")
next_field = next_patient_field(active_session)

if not pending_field and next_field:
    prompt = patient_prompt(next_field)
    if prompt:
        active_session["pending_patient_field"] = next_field
        active_session["messages"].append({"role": "assistant", "content": prompt})
        with st.chat_message("assistant"):
            st.markdown(prompt)

user_input = st.chat_input("", disabled=st.session_state.busy)

pending_field = active_session.get("pending_patient_field")
if user_input and not st.session_state.busy:
    st.session_state.pending_user_input = user_input
    if not pending_field:
        st.session_state.busy = True
        st.rerun()

if st.session_state.pending_user_input:
    user_input = st.session_state.pending_user_input

if user_input:
    pending_field = active_session.get("pending_patient_field")
    if pending_field:
        active_session["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        if pending_field == "patient_id":
            active_session["patient_id"] = user_input.strip()
        elif pending_field == "age":
            try:
                age_value = int(user_input.strip())
                if age_value < 0 or age_value > 120:
                    raise ValueError("Age out of range")
                active_session["age"] = age_value
            except ValueError:
                prompt = "Please enter a valid age as a number (0-120)."
                active_session["messages"].append({"role": "assistant", "content": prompt})
                with st.chat_message("assistant"):
                    st.markdown(prompt)
                st.session_state.pending_user_input = None
                st.session_state.busy = False
                st.rerun()
        elif pending_field == "gender":
            active_session["gender"] = user_input.strip()

        active_session["pending_patient_field"] = None
        next_field = next_patient_field(active_session)
        if next_field:
            prompt = patient_prompt(next_field)
            active_session["pending_patient_field"] = next_field
            active_session["messages"].append({"role": "assistant", "content": prompt})
            with st.chat_message("assistant"):
                st.write_stream(stream_text(prompt))
        else:
            enqueue_symptom_prompt(active_session)
        st.session_state.pending_user_input = None
        st.session_state.busy = False
        st.rerun()

    active_session["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    try:
        with st.spinner("Analyzing..."):
            extraction_start = time.perf_counter()
            response = triage_agent.invoke(build_extraction_prompt(user_input))
            output = response.content
            data = parse_llm_output(output)
            data = sanitize_extraction(user_input, data)

            if "error" in data:
                response = triage_agent.invoke(build_extraction_prompt(user_input))
                output = response.content
                data = parse_llm_output(output)
                data = sanitize_extraction(user_input, data)

            extraction_elapsed = time.perf_counter() - extraction_start

            if "error" in data:
                with st.chat_message("assistant"):
                    st.error("Could not parse the model output. Try rephrasing the input.")
                    st.caption(f"Extraction time: {extraction_elapsed:.2f}s")
                st.session_state.pending_user_input = None
                st.session_state.busy = False
                st.rerun()

            active_session["state"] = update_state(active_session["state"], data)

            if not is_enough_info(active_session["state"]):
                question = get_followup_question(active_session["state"])
                active_session["messages"].append({"role": "assistant", "content": question})
                with st.chat_message("assistant"):
                    st.write_stream(stream_text(question))
                    st.caption(f"Extraction time: {extraction_elapsed:.2f}s")
                st.session_state.pending_user_input = None
                st.session_state.busy = False
                st.rerun()

            result = hybrid_triage(active_session["state"], int(active_session.get("age") or 0))
            suggested_action = suggested_action_for_urgency(result["urgency"])

            format_start = time.perf_counter()
            formatted = format_triage(
                formatter_agent,
                result["urgency"],
                active_session["state"]["symptoms"],
                active_session["state"].get("duration"),
                suggested_action,
            )
            format_elapsed = time.perf_counter() - format_start

            active_session["messages"].append({"role": "assistant", "content": formatted})

            with st.chat_message("assistant"):
                st.write_stream(stream_text(formatted))
                st.caption(
                    f"Extraction time: {extraction_elapsed:.2f}s | Format time: {format_elapsed:.2f}s"
                )
    finally:
        st.session_state.pending_user_input = None
        st.session_state.busy = False
