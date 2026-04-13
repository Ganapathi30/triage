from dotenv import load_dotenv
from langchain_ollama import ChatOllama

load_dotenv()

FORMAT_PROMPT = """
You are a medical triage formatter.

You will be given:
- urgency level
- symptoms

Your job:
Format output EXACTLY like below:

Urgency Level: <value>

Reasoning Summary:
<clear short explanation based on symptoms>

Suggested Action:
<appropriate action>

Disclaimer:
This is not a medical diagnosis. This is only a triage assessment.

RULES:
- DO NOT change urgency
- DO NOT add diagnosis
- DO NOT invent symptoms
- DO NOT add new symptoms
- Avoid diagnosis statements
- Avoid treatment instructions
- Never suggest medication
- Keep it short and clear
- DO NOT remove disclaimer
- Keep meaning EXACTLY the same
"""

def create_formatter_agent():
    llm = ChatOllama(model="qwen3.5",
        base_url="https://ollama.com",)
    return llm


def format_triage(llm, urgency, symptoms):
    prompt = (
        FORMAT_PROMPT
        + "\n\n"
        + f"Urgency: {urgency}\n"
        + f"Symptoms: {symptoms}\n"
    )
    response = llm.invoke(prompt)
    return response.content