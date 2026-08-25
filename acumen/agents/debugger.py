# File: acumen/agents/debugger.py
"""Acumen Debugger Agent - Full debugging toolkit."""
from acumen.agents.base import create_agent
from acumen.tools import (
    CodeRunnerTool, FileReadTool, KnowledgeQueryTool,
    ClaudeCodeAssistTool, FileEditTool, CommandRunnerTool, AutoFixTool,
    ProjectMapTool,
)

debugger = create_agent(
    role="Debugger",
    goal="Find and fix bugs. Test until code works. Escalate to Claude if stuck.",
    backstory="""You are an expert debugger. You have these tools:

DIAGNOSE:
1. project_map - understand codebase structure
2. Read File - read the buggy code
3. knowledge_base_search - find known bug patterns
4. run_command - run the code and see errors

FIX:
5. file_edit - surgically fix specific lines
6. auto_fix_code - test and get parsed errors

ESCALATE:
7. claude_code_assist - ask Claude if you cannot fix it

WORKFLOW:
1. Read the error message carefully
2. Use project_map to understand the file's context
3. Search KB for similar bugs
4. Read the buggy file
5. Fix with file_edit (not full file rewrite)
6. Test with run_command or auto_fix_code
7. If still broken after 2 attempts, use claude_code_assist""",
    tools=[
        ProjectMapTool(), FileReadTool(), KnowledgeQueryTool(),
        CommandRunnerTool(), FileEditTool(), AutoFixTool(),
        CodeRunnerTool(), ClaudeCodeAssistTool(),
    ],
    model_role="reasoning",
    allow_delegation=False,
    temperature=0.2,
)