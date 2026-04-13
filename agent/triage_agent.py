from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from agent.system_prompt import SYSTEM_PROMPT

def create_triage_agent(checkpointer):
    llm = ChatOllama(
        model = "llama3.2:1b",
        temperature=0.1,
    )

    agent = create_agent(
        model=llm,
        system_prompt=SYSTEM_PROMPT,
    )

    return agent