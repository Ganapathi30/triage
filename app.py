from agent import formatter_agent
from agent.triage_agent import create_triage_agent
from langgraph.checkpoint.postgres import PostgresSaver
from config import DB_URI
from services.extractor import parse_llm_output

import time

from services.triage_engine import hybrid_triage

def stream_text(text):
    for char in text:
        print(char, end="", flush=True)
        time.sleep(0.01)  

        
with PostgresSaver.from_conn_string(DB_URI) as checkpointer:

    checkpointer.setup()

    agent = create_triage_agent(checkpointer)

    patient_id = input("Enter patient ID:")
    age = input("Enter patient's age:")
    gender = input("Enter patient's gender:")

    print("Enter the primary symptoms the patient is experincing:")

    while True:
        user_input = input(f"[{patient_id}] You: ")

        if user_input.lower() == "exit":
            break

        print("Agent called")
        response = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            {"configurable": {"thread_id": patient_id}}
        )
        print("Agent responded")

        output = response["messages"][-1].content
        data = parse_llm_output(output)

        print(data)

        if "error" in data:
            print("Error")
            print("RAW OUTPUT:\n", output)
            continue

        if not data["has_enough_info"]:
            print("AI: ", end="")
            stream_text(data["follow_up_question"])
            print()

        else:
            result = hybrid_triage(data, int(age))
            print(result)
            
            formatter = formatter_agent()

            for chunk in formatter.stream(
            {
                "messages": [{
                        "role": "user",
                        "content": f"""
            Urgency: {result['urgency']}
            Symptoms: {result['symptoms']}
            """
                    }]
                }
            ):
                if "messages" in chunk:
                    msg = chunk["messages"][-1]
                    if hasattr(msg, "content") and msg.content:
                        print(msg.content, end="", flush=True)

            print()





       
