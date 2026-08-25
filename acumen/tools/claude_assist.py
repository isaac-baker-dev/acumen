"""
Acumen Claude Code Assist Tool
================================
When local code models can't solve a problem, this tool escalates to Claude.
Every response gets saved to the knowledge base so Acumen learns over time.

The apprenticeship model:
1. Local model tries first (fast, free, private)
2. If stuck → sends code + error to Claude (smart, accurate)
3. Claude's fix is stored in KB (Acumen learns the pattern)
4. Next time a similar problem appears → local model finds it in KB
5. Over time, Acumen needs Claude less and less
"""

from typing import Any
from crewai.tools import BaseTool
from acumen.core.config import is_cloud_available
from acumen.core.logger import get_logger
from acumen.memory import MemoryManager

logger = get_logger("acumen.tools.claude_assist")


class ClaudeCodeAssistTool(BaseTool):
    name: str = "claude_code_assist"
    description: str = (
        "Escalate a difficult coding problem to Claude AI for help. "
        "Use this ONLY when you cannot solve the problem yourself. "
        "Input: describe the problem, include any error messages and "
        "your attempted code. Claude will return a fix and explanation."
    )

    def _run(self, **kwargs: Any) -> str:
        # Extract the problem description from whatever the LLM sent
        problem = ""
        for key, val in kwargs.items():
            if val and isinstance(val, str) and len(val.strip()) > 1:
                problem = str(val).strip()
                break

        if not problem:
            return "Describe the coding problem you need help with."

        if not is_cloud_available():
            return (
                "Claude API not available. No API key configured. "
                "Try solving this with knowledge_base_search for similar patterns."
            )

        try:
            from litellm import completion

            logger.info(f"Escalating to Claude: {problem[:80]}...")

            # Build a focused coding prompt
            prompt = (
                "You are an expert software engineer helping a local AI coding agent. "
                "The agent is stuck on a problem and needs your help.\n\n"
                "RULES:\n"
                "- Provide COMPLETE working code, not fragments\n"
                "- Include all imports\n"
                "- Add comments explaining the fix\n"
                "- Explain WHY the original approach failed\n"
                "- If the code is Rust or Go, make it compile-ready\n"
                "- Keep explanations concise\n\n"
                f"PROBLEM:\n{problem[:3000]}\n\n"
                "Provide your solution:"
            )

            response = completion(
                model="claude-sonnet-4-20250514",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=4000,
            )

            solution = response.choices[0].message.content

            # Save to knowledge base for future learning
            memory = MemoryManager()
            try:
                # Save the problem-solution pair
                kb_entry = (
                    f"CODING PROBLEM:\n{problem[:500]}\n\n"
                    f"CLAUDE SOLUTION:\n{solution[:2000]}"
                )
                memory.save_knowledge(
                    kb_entry,
                    {
                        "source": "claude_code_assist",
                        "topic": "code_pattern",
                        "problem_type": _classify_problem(problem),
                        "language": _detect_language(problem),
                    },
                )
                memory.save_episode(
                    "claude_assist",
                    f"Problem: {problem[:300]}",
                    {
                        "solution_length": len(solution),
                        "language": _detect_language(problem),
                    },
                )
                logger.info("Claude solution saved to knowledge base for future learning")
            except Exception as e:
                logger.warning(f"Could not save to KB: {e}")

            return (
                f"CLAUDE'S SOLUTION:\n\n{solution}\n\n"
                "[This solution has been saved to the knowledge base. "
                "Next time a similar problem appears, check knowledge_base_search first.]"
            )

        except Exception as e:
            logger.error(f"Claude assist failed: {e}")
            return f"Claude assist failed: {str(e)[:200]}. Try knowledge_base_search for similar patterns."


class ClaudeCodeReviewTool(BaseTool):
    name: str = "claude_code_review"
    description: str = (
        "Send code to Claude for expert review. Use this after writing code "
        "to get feedback on bugs, security issues, and improvements. "
        "Input: the code to review."
    )

    def _run(self, **kwargs: Any) -> str:
        code = ""
        for key, val in kwargs.items():
            if val and isinstance(val, str) and len(val.strip()) > 1:
                code = str(val).strip()
                break

        if not code:
            return "Provide the code you want reviewed."

        if not is_cloud_available():
            return "Claude API not available. Review the code manually for common issues."

        try:
            from litellm import completion

            logger.info("Sending code to Claude for review...")

            prompt = (
                "Review this code. Be concise. Format your response as:\n\n"
                "BUGS: (list any bugs found, or 'None')\n"
                "SECURITY: (any security issues, or 'None')\n"
                "IMPROVEMENTS: (top 3 suggestions)\n"
                "FIXED CODE: (only if bugs were found, otherwise skip)\n\n"
                f"CODE:\n{code[:4000]}"
            )

            response = completion(
                model="claude-sonnet-4-20250514",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=3000,
            )

            review = response.choices[0].message.content

            # Save review patterns to KB
            memory = MemoryManager()
            try:
                memory.save_knowledge(
                    f"CODE REVIEW PATTERN:\n{code[:300]}\n\nREVIEW:\n{review[:1000]}",
                    {
                        "source": "claude_code_review",
                        "topic": "code_review_pattern",
                        "language": _detect_language(code),
                    },
                )
            except:
                pass

            return f"CLAUDE'S REVIEW:\n\n{review}"

        except Exception as e:
            return f"Review failed: {str(e)[:200]}"


def _classify_problem(text):
    """Simple problem classification for KB tagging."""
    text_lower = text.lower()
    if "error" in text_lower or "traceback" in text_lower:
        return "bug_fix"
    if "compile" in text_lower or "build" in text_lower:
        return "compilation"
    if "test" in text_lower:
        return "testing"
    if "design" in text_lower or "architect" in text_lower:
        return "architecture"
    if "optimize" in text_lower or "performance" in text_lower:
        return "optimization"
    return "general"


def _detect_language(text):
    """Detect programming language from code/problem text."""
    text_lower = text.lower()
    if "rust" in text_lower or "cargo" in text_lower or "fn main" in text_lower:
        return "rust"
    if "golang" in text_lower or "go " in text_lower or "func main" in text_lower:
        return "go"
    if "python" in text_lower or "def " in text_lower or "import " in text_lower:
        return "python"
    if "javascript" in text_lower or "const " in text_lower or "function " in text_lower:
        return "javascript"
    return "unknown"
