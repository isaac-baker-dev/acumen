# File: acumen/agents/researcher.py
"""Acumen Research Analyst Agent"""
from acumen.agents.base import create_agent
from acumen.tools import KnowledgeQueryTool, WebSearchTool

researcher = create_agent(
    role="Research Analyst",
    goal="Find accurate information using your tools.",
    backstory="""You are a research assistant. You have TWO tools:
1. knowledge_base_search - search the local knowledge base
2. web_search - search the internet

RULES:
- Use knowledge_base_search FIRST with a short query (3-6 words)
- Then use web_search ONCE with different short keywords
- Then write your final answer with what you found
- NEVER use the same query twice
- NEVER call tools more than 3 times total""",
    tools=[KnowledgeQueryTool(), WebSearchTool()],
    model_role="reasoning",
    allow_delegation=False,
    temperature=0.3,
)