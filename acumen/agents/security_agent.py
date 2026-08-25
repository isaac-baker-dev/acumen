# File: acumen/agents/security_agent.py
"""Acumen Security Analyst Agent"""

from acumen.agents.base import create_agent
from acumen.tools import FileReadTool, KnowledgeQueryTool

security_agent = create_agent(
    role="Security Analyst",
    goal="Monitor actions for safety and policy compliance.",
    backstory="""You are the Acumen Security Agent. Non-negotiable rules:
1. BLOCK unlisted commands
2. BLOCK unauthorized file access
3. LOG every blocked action
4. ALERT on repeated violations""",
    tools=[FileReadTool(), KnowledgeQueryTool()],
    model_role="fast",
    allow_delegation=False,
    temperature=0.1,
)