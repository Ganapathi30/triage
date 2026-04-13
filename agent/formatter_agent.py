from langchain.agents import create_agent
from langchain_ollama import ChatOllama

FORMAT_PROMPT = """
You are a medical triage formatter.

You will be given:
- urgency level
- symptoms

Your job:
Format output EXACTLY like below:

🟥 / 🟨 / 🟩 Urgency Level: <value>

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
- Keep it short and clear
- DO NOT remove disclaimer
- Keep meaning EXACTLY the same
"""

def create_formatter_agent():
    llm = ChatOllama(model="llama3:8b", streaming=True)

    agent = create_agent(
        model=llm,
        system_prompt=FORMAT_PROMPT
    )

    return agent