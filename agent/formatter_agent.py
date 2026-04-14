from dotenv import load_dotenv
from langchain_ollama import ChatOllama

load_dotenv()

FORMAT_PROMPT = """
You are a medical triage formatter.

You will be given:
- urgency level (already decided)
- symptoms (list)
- duration (text)
- suggested action (already decided)

Your job:
Rephrase and format the information into clear, structured output.

Output EXACTLY in this format:

Urgency: <urgency level>

Reasoning:
1. The patient is experiencing <symptom 1> for <duration>
2. <symptom 2> reported
3. <symptom 3> reported

Suggested Action:
<rephrased suggested action>

⚠️ This triage assistant does not diagnose or replace medical professionals.

RULES:
- DO NOT change urgency level
- DO NOT add new symptoms
- DO NOT remove symptoms
- DO NOT add diagnosis or medical conditions
- DO NOT suggest medications
- DO NOT infer anything beyond given inputs
- Keep wording simple and clear
- Convert symptoms into natural sentences
- Include duration naturally in at least one reasoning point
- Keep Suggested Action short and rephrased only
- Output must strictly follow the format
"""

def create_formatter_agent():
    llm = ChatOllama(
        model="llama3.2:3b-instruct-q4_K_M",
        base_url="http://localhost:11434",
        temperature=0,
    )
    return llm


def format_triage(llm, urgency, symptoms, duration, suggested_action):
    prompt = (
        FORMAT_PROMPT
        + "\n\n"
        + f"Urgency: {urgency}\n"
        + f"Symptoms: {symptoms}\n"
        + f"Duration: {duration}\n"
        + f"Suggested Action: {suggested_action}\n"
    )
    response = llm.invoke(prompt)
    return response.content