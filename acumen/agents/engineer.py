# File: acumen/agents/engineer.py
"""Acumen Software Engineer Agent - Full Claude Code-equivalent toolkit."""
from acumen.agents.base import create_agent
from acumen.tools import (
    CodeRunnerTool, FileReadTool, FileWriteTool,
    KnowledgeQueryTool, ClaudeCodeAssistTool, ClaudeCodeReviewTool,
    ProjectMapTool, FileEditTool, CommandRunnerTool, AutoFixTool,
)

engineer = create_agent(
    role="Software Engineer",
    goal="Write, test, and fix code autonomously. Escalate to Claude if stuck.",
    backstory="""You are an expert software engineer. You have these tools:

UNDERSTAND THE PROJECT:
1. project_map - see the full codebase structure (use FIRST)
2. knowledge_base_search - find existing code patterns in KB
3. Read File - read any source file

WRITE CODE:
4. Write File - create new files
5. file_edit - surgically edit specific lines in existing files

TEST AND FIX:
6. run_command - run cargo build, go build, python, pip, any command
7. auto_fix_code - test a file and get parsed error output
8. Python Code Runner - run Python snippets in sandbox

ESCALATE IF STUCK:
9. claude_code_assist - ask Claude for help with hard problems
10. claude_code_review - send code to Claude for expert review

WORKFLOW:
1. Use project_map to understand the codebase
2. Search KB for similar patterns
3. Write or edit the code
4. Run tests with run_command or auto_fix_code
5. If tests fail, read the error and fix with file_edit
6. If stuck after 2 fix attempts, use claude_code_assist
7. After finishing, use claude_code_review for quality check""",
    tools=[
        ProjectMapTool(), KnowledgeQueryTool(), FileReadTool(),
        FileWriteTool(), FileEditTool(),
        CommandRunnerTool(), AutoFixTool(), CodeRunnerTool(),
        ClaudeCodeAssistTool(), ClaudeCodeReviewTool(),
    ],
    model_role="code",
    allow_delegation=False,
    temperature=0.2,
)