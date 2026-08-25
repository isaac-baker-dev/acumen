"""Acumen Agent Factory - Consistent agent creation."""
from crewai import Agent, LLM
from acumen.core.config import AGENT_MAX_ITER, AGENT_VERBOSE, MODELS, OLLAMA_BASE_URL

def create_agent(role, goal, backstory, tools=None,
                 model_role="reasoning", temperature=None,
                 allow_delegation=False):
    model_name = MODELS.get(model_role, MODELS["reasoning"])
    temp = temperature if temperature is not None else 0.3
    llm = LLM(
        model=f"ollama/{model_name}",
        base_url=OLLAMA_BASE_URL,
        temperature=temp,
    )
    return Agent(
        role=role, goal=goal, backstory=backstory,
        tools=tools or [],
        llm=llm,
        max_iter=AGENT_MAX_ITER,
        verbose=AGENT_VERBOSE,
        allow_delegation=allow_delegation,
        memory=False,
    )