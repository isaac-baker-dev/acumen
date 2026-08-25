"""Acumen Code Reviewer - Reviews code for bugs, security, and quality."""

from acumen.core.llm import get_llm
from acumen.core.logger import get_logger

logger = get_logger("acumen.agents.reviewer")

def review_code(code, language="python"):
    llm = get_llm("fast")
    prompt = (
        f"Review this {language} code briefly. List any bugs, security issues, or improvements.\n\n"
        f"```{language}\n{code}\n```\n\n"
        "Give a short review with the top 3-5 issues:"
    )
    try:
        review = llm.invoke(prompt)
        logger.info(f"Code review completed: {len(code)} chars reviewed")
        return review
    except Exception as e:
        logger.warning(f"Code review failed: {e}")
        return f"Review failed: {str(e)}"

def review_file(file_path):
    from pathlib import Path
    path = Path(file_path)
    if not path.exists():
        return f"File not found: {file_path}"
    ext_map = {".py": "python", ".js": "javascript", ".ts": "typescript",
               ".rs": "rust", ".go": "go", ".java": "java", ".cpp": "cpp",
               ".c": "c", ".rb": "ruby", ".php": "php", ".swift": "swift"}
    language = ext_map.get(path.suffix.lower(), "unknown")
    code = path.read_text(encoding="utf-8", errors="replace")
    if len(code) > 3000:
        code = code[:3000] + "\n\n... (truncated)"
    return review_code(code, language)