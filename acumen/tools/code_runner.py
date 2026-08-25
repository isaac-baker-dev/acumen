# File: acumen/tools/code_runner.py
from crewai.tools import BaseTool
from acumen.security.sandbox import run_code_sandboxed

class CodeRunnerTool(BaseTool):
    name: str = "Python Code Runner"
    description: str = "Run Python in sandbox. Input: code string."

    def _run(self, code: str) -> str:
        r = run_code_sandboxed(code)
        out = ""
        if r["stdout"]: out += f"Output:\n{r['stdout']}"
        if r["stderr"]: out += f"\nErrors:\n{r['stderr']}"
        if r["timed_out"]: out += "\n[TIMEOUT]"
        return out or "Executed (no output)."