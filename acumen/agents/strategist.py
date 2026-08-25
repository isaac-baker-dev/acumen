# File: acumen/agents/strategist.py
"""Acumen Strategist Agent"""
from acumen.agents.base import create_agent
from acumen.tools import KnowledgeQueryTool

strategist = create_agent(
    role="Strategist",
    goal="Synthesize research into clear summaries with actionable next steps.",
    backstory="""You are a strategist. You have ONE tool:
1. knowledge_base_search - search the local knowledge base

RULES:
- Use knowledge_base_search ONCE if you need background info
- Then write your synthesis based on the task context provided
- Keep summaries clear: Top 3 findings, then Next Steps
- Do NOT call tools more than 2 times""",
    tools=[KnowledgeQueryTool()],
    model_role="reasoning",
    allow_delegation=False,
    temperature=0.3,
)