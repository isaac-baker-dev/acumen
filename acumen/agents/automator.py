# File: acumen/agents/automator.py
"""Acumen Automation Engineer Agent"""

from acumen.agents.base import create_agent
from acumen.tools import FileWriteTool, KnowledgeQueryTool

automator = create_agent(
    role="Automation Engineer",
    goal="Build DAG pipelines for automated workflows.",
    backstory="""You are the Acumen Automator. Rules:
1. Every pipeline has error handling
2. Long tasks log progress
3. Include notification on completion""",
    tools=[FileWriteTool(), KnowledgeQueryTool()],
    model_role="fast",
    allow_delegation=False,
    temperature=0.2,
)