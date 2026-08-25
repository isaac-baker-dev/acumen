# File: acumen/agents/knowledge_agent.py
"""Acumen Knowledge Archivist Agent"""

from acumen.agents.base import create_agent
from acumen.tools import KnowledgeQueryTool, FileReadTool, WebSearchTool

knowledge_agent = create_agent(
    role="Knowledge Archivist",
    goal="Curate and maintain the Acumen knowledge base.",
    backstory="""You are the Acumen Archivist. Protocol:
1. Check for duplicates before ingesting
2. Add metadata: source, date, topic, quality
3. Summarize each document
4. Track coverage gaps""",
    tools=[KnowledgeQueryTool(), FileReadTool(), WebSearchTool()],
    model_role="reasoning",
    allow_delegation=False,
    temperature=0.3,
)