from dotenv import load_dotenv
from langchain_ollama import ChatOllama

from agent.system_prompt import SYSTEM_PROMPT

load_dotenv()

def create_triage_agent():
    llm = ChatOllama(
        model="qwen2.5:3b",
        base_url="http://localhost:11434",
        system_prompt=SYSTEM_PROMPT,
        temperature=0,
        format="json",
    )
    return llm