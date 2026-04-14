import time

import streamlit as st

from agent.triage_agent import create_triage_agent
from agent.formatter_agent import create_formatter_agent, format_triage
from services.extractor import parse_llm_output
from services.triage_engine import hybrid_triage
from core.state import update_state
from core.logic import is_enough_info, get_followup_question
from services.helpers import (
    build_extraction_prompt,
    sanitize_extraction,
    ensure_sessions,
    get_active_session,
    render_sidebar,
    next_patient_field,
    patient_prompt,
    enqueue_symptom_prompt,
    suggested_action_for_urgency,
    stream_text,
)


APP_TITLE = "Triage Agent"


@st.cache_resource
def get_agents():
    return create_triage_agent(), create_formatter_agent()


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
                followup_payload = {
                    "text": question,
                    "extraction_elapsed": extraction_elapsed,
                }
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

            response_payload = {
                "text": formatted,
                "extraction_elapsed": extraction_elapsed,
                "format_elapsed": format_elapsed,
            }

        with st.chat_message("assistant"):
            st.write_stream(stream_text(response_payload["text"]))
            st.caption(
                "Extraction time: "
                f"{response_payload['extraction_elapsed']:.2f}s | "
                "Format time: "
                f"{response_payload['format_elapsed']:.2f}s"
            )
    finally:
        st.session_state.pending_user_input = None
        st.session_state.busy = False
