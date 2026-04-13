from agent.triage_agent import create_triage_agent
from agent.formatter_agent import create_formatter_agent, format_triage
from services.extractor import parse_llm_output
from services.triage_engine import hybrid_triage
from core.state import init_state, update_state
from core.logic import is_enough_info, get_followup_question

import time

STREAM_DELAY_SECONDS = 0.0


def stream_text(text):
    for char in text:
        print(char, end="", flush=True)
        if STREAM_DELAY_SECONDS > 0:
            time.sleep(STREAM_DELAY_SECONDS)


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


def main():
    agent = create_triage_agent()
    formatter = create_formatter_agent()

    patient_id = input("Enter patient ID: ")
    age = int(input("Enter patient's age: "))
    gender = input("Enter patient's gender: ")

    state = init_state()

    print("Enter patient symptoms:")

    while True:
        user_input = input(f"[{patient_id}] You: ")

        if user_input.lower() == "exit":
            break

        # 🔹 LLM extraction
        extraction_start = time.perf_counter()
        response = agent.invoke(build_extraction_prompt(user_input))
        output = response.content
        data = parse_llm_output(output)

        if "error" in data:
            response = agent.invoke(build_extraction_prompt(user_input))
            output = response.content
            data = parse_llm_output(output)

        extraction_elapsed = time.perf_counter() - extraction_start

        if "error" in data:
            print(f"Extraction time: {extraction_elapsed:.2f}s")
            print("Error parsing LLM output:", output)
            continue

        # 🔹 Update state
        state = update_state(state, data)

        # 🔹 Check if enough info
        if not is_enough_info(state):
            question = get_followup_question(state)
            print("AI: ", end="")
            stream_text(question)
            print()
            continue

        # 🔹 Run triage engine
        result = hybrid_triage(state, age)

        # 🔹 Formatter agent
        format_start = time.perf_counter()
        formatted = format_triage(
            formatter,
            result["urgency"],
            state["symptoms"],
        )
        format_elapsed = time.perf_counter() - format_start
        stream_text(formatted)
        print()
        print(f"Extraction time: {extraction_elapsed:.2f}s | Format time: {format_elapsed:.2f}s")
        break


if __name__ == "__main__":
    main()