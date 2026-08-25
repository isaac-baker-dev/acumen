# File: acumen/agents/crews.py
"""Acumen Agent Crews - All agents connected to the DAG pipeline system."""
from crewai import Task, Crew, Process
from acumen.agents.strategist import strategist
from acumen.agents.researcher import researcher
from acumen.agents.engineer import engineer
from acumen.agents.debugger import debugger
from acumen.agents.knowledge_agent import knowledge_agent
from acumen.agents.security_agent import security_agent
from acumen.agents.automator import automator


def research_crew(topic):
    """Research + Strategist synthesis."""
    t1 = Task(description=f"Research: {topic}",
              expected_output="Research brief with sources",
              agent=researcher)
    t2 = Task(description="Synthesize into executive summary",
              expected_output="Top 3 takeaways + next steps",
              agent=strategist, context=[t1])
    return Crew(agents=[researcher, strategist], tasks=[t1, t2],
                process=Process.sequential, verbose=True)


def coding_crew(spec):
    """Research → Engineer → Debugger pipeline."""
    t1 = Task(description=f"Research best practices: {spec}",
              expected_output="Technical brief", agent=researcher)
    t2 = Task(description=f"Write code: {spec}. Include tests.",
              expected_output="Working code with tests",
              agent=engineer, context=[t1])
    t3 = Task(description="Review for bugs and security issues",
              expected_output="Review with fix suggestions",
              agent=debugger, context=[t2])
    return Crew(agents=[researcher, engineer, debugger],
                tasks=[t1, t2, t3], process=Process.sequential, verbose=True)


def learning_crew(topic):
    """Research → Strategy → Knowledge archival."""
    t1 = Task(description=f"Research '{topic}' comprehensively",
              expected_output="Detailed brief", agent=researcher)
    t2 = Task(description="Create learning guide with exercises",
              expected_output="Complete learning guide",
              agent=strategist, context=[t1])
    t3 = Task(description="Archive key facts to knowledge base",
              expected_output="KB update confirmation",
              agent=knowledge_agent, context=[t2])
    return Crew(agents=[researcher, strategist, knowledge_agent],
                tasks=[t1, t2, t3], process=Process.sequential, verbose=True)


def security_crew(target):
    """Security audit pipeline — Security Agent + Debugger."""
    t1 = Task(description=f"Security audit: {target}",
              expected_output="Security report with vulnerabilities found",
              agent=security_agent)
    t2 = Task(description="Review findings and suggest fixes",
              expected_output="Fix recommendations with priority",
              agent=debugger, context=[t1])
    return Crew(agents=[security_agent, debugger],
                tasks=[t1, t2], process=Process.sequential, verbose=True)


def automation_crew(task_desc):
    """Automation pipeline — Automator designs, Engineer builds."""
    t1 = Task(description=f"Design automation for: {task_desc}",
              expected_output="Automation plan with steps and schedule",
              agent=automator)
    t2 = Task(description="Implement the automation scripts",
              expected_output="Working automation code",
              agent=engineer, context=[t1])
    t3 = Task(description="Security review of automation",
              expected_output="Security clearance or issues",
              agent=security_agent, context=[t2])
    return Crew(agents=[automator, engineer, security_agent],
                tasks=[t1, t2, t3], process=Process.sequential, verbose=True)


def full_build_crew(spec):
    """Full pipeline — ALL agents: Research → Strategy → Code → Debug → Security → Archive."""
    t1 = Task(description=f"Research: {spec}",
              expected_output="Technical research brief",
              agent=researcher)
    t2 = Task(description=f"Create build strategy for: {spec}",
              expected_output="Step-by-step build plan",
              agent=strategist, context=[t1])
    t3 = Task(description=f"Write the code: {spec}",
              expected_output="Complete working code",
              agent=engineer, context=[t2])
    t4 = Task(description="Debug and fix any issues",
              expected_output="Bug-free code",
              agent=debugger, context=[t3])
    t5 = Task(description="Security audit of the code",
              expected_output="Security clearance",
              agent=security_agent, context=[t4])
    t6 = Task(description="Archive everything to knowledge base",
              expected_output="KB updated with all artifacts",
              agent=knowledge_agent, context=[t5])
    return Crew(
        agents=[researcher, strategist, engineer, debugger, security_agent, knowledge_agent],
        tasks=[t1, t2, t3, t4, t5, t6],
        process=Process.sequential, verbose=True)