"""
Acumen Advanced Coding Tools
==============================
These tools give agents Claude Code-like capabilities:
1. ProjectMapTool - See full codebase structure
2. FileEditTool - Surgical find-and-replace editing
3. CommandRunnerTool - Run any terminal command (cargo, go, pip, etc.)
4. AutoFixTool - Try code → run → parse error → fix → retry loop

Combined with ClaudeCodeAssistTool for escalation, these make
Acumen's agents capable of autonomous coding and debugging.
"""

import os
import subprocess
import re
from typing import Any
from pathlib import Path
from crewai.tools import BaseTool
from acumen.core.logger import get_logger

logger = get_logger("acumen.tools.advanced_coding")

# Safety: directories agents are allowed to access
ALLOWED_DIRS = [
    str(Path.home() / "acumen"),
]

BLOCKED_COMMANDS = [
    "rm -rf /", "format", "del /s /q", "rmdir /s",
    "shutdown", "restart", "reboot",
    "curl | bash", "curl | sh", "wget | bash",
    "powershell -enc", "iex(", "invoke-expression",
]


def is_safe_path(filepath):
    """Check if a path is within allowed directories."""
    resolved = str(Path(filepath).resolve())
    return any(resolved.startswith(str(Path(d).resolve())) for d in ALLOWED_DIRS)


def is_safe_command(command):
    """Check if a command is safe to run."""
    cmd_lower = command.lower().strip()
    return not any(blocked in cmd_lower for blocked in BLOCKED_COMMANDS)


class ProjectMapTool(BaseTool):
    name: str = "project_map"
    description: str = (
        "See the full project directory structure. Shows all files and folders "
        "in the Acumen project. Use this FIRST when you need to understand "
        "the codebase before making changes. "
        "Input: a directory path (default: the acumen project root), or 'focused' "
        "for just the Python source files."
    )

    def _run(self, **kwargs: Any) -> str:
        path = ""
        for key, val in kwargs.items():
            if val and isinstance(val, str):
                path = str(val).strip()
                break

        project_root = Path.home() / "acumen"

        if not path or path in (".", "root", "all", "acumen"):
            target = project_root
        elif path == "focused":
            return self._focused_map(project_root)
        else:
            target = Path(path)
            if not target.is_absolute():
                target = project_root / path

        if not is_safe_path(str(target)):
            return f"Access denied: {target}"

        if not target.exists():
            return f"Path not found: {target}"

        return self._build_tree(target, max_depth=3)

    def _build_tree(self, root, max_depth=3, prefix="", depth=0):
        if depth >= max_depth:
            return ""

        output = ""
        try:
            items = sorted(root.iterdir(), key=lambda x: (x.is_file(), x.name))
        except PermissionError:
            return f"{prefix}[permission denied]\n"

        # Skip common non-essential dirs
        skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv",
                     "target", ".mypy_cache", ".pytest_cache", "dist", ".egg-info"}

        dirs = [i for i in items if i.is_dir() and i.name not in skip_dirs]
        files = [i for i in items if i.is_file()]

        for f in files:
            size = f.stat().st_size
            size_str = f"{size}B" if size < 1024 else f"{size//1024}KB"
            output += f"{prefix}{f.name} ({size_str})\n"

        for d in dirs:
            output += f"{prefix}{d.name}/\n"
            output += self._build_tree(d, max_depth, prefix + "  ", depth + 1)

        return output

    def _focused_map(self, root):
        """Show only Python source files with their first docstring."""
        output = "ACUMEN SOURCE FILES:\n\n"

        src_dir = root / "acumen"
        if not src_dir.exists():
            return "Source directory not found."

        for py_file in sorted(src_dir.rglob("*.py")):
            if "__pycache__" in str(py_file):
                continue
            rel = py_file.relative_to(root)
            # Get first line or docstring
            try:
                first_lines = py_file.read_text(encoding="utf-8", errors="ignore").split("\n")[:3]
                desc = ""
                for line in first_lines:
                    line = line.strip().strip('"').strip("'")
                    if line and not line.startswith("#") and not line.startswith("from") and not line.startswith("import"):
                        desc = line[:60]
                        break
                output += f"  {rel}"
                if desc:
                    output += f"  # {desc}"
                output += "\n"
            except:
                output += f"  {rel}\n"

        # Also show Rust and Go files
        engine_dir = root / "engine"
        if engine_dir.exists():
            output += "\nENGINE FILES:\n"
            for ext in ["*.rs", "*.go", "*.toml", "*.mod"]:
                for f in sorted(engine_dir.rglob(ext)):
                    if "target" not in str(f):
                        output += f"  {f.relative_to(root)}\n"

        return output


class FileEditTool(BaseTool):
    name: str = "file_edit"
    description: str = (
        "Edit a file by finding and replacing specific text. Much better than "
        "rewriting entire files. Input as JSON with three fields: "
        "filepath (the file to edit), find (the exact text to find), "
        "replace (the new text to put in its place). "
        "Example: {\"filepath\": \"acumen/agents/researcher.py\", "
        "\"find\": \"temperature=0.4\", \"replace\": \"temperature=0.3\"}"
    )

    def _run(self, **kwargs: Any) -> str:
        filepath = kwargs.get("filepath", kwargs.get("file", ""))
        find_text = kwargs.get("find", kwargs.get("old", kwargs.get("search", "")))
        replace_text = kwargs.get("replace", kwargs.get("new", kwargs.get("replacement", "")))

        # Handle case where all args come as one string
        if not filepath:
            for key, val in kwargs.items():
                if isinstance(val, str) and ("/" in val or "\\" in val):
                    filepath = val
                    break

        if not filepath:
            return "Provide filepath, find, and replace parameters."

        # Resolve path
        path = Path(filepath)
        if not path.is_absolute():
            path = Path.home() / "acumen" / filepath

        if not is_safe_path(str(path)):
            return f"Access denied: {path}"

        if not path.exists():
            return f"File not found: {path}"

        try:
            content = path.read_text(encoding="utf-8")

            if not find_text:
                return f"File exists ({len(content)} chars). Provide 'find' text to search for."

            if find_text not in content:
                # Try to find close matches
                lines = content.split("\n")
                close = [l.strip() for l in lines if find_text[:20] in l]
                hint = f"\nClose matches:\n" + "\n".join(close[:3]) if close else ""
                return f"Text not found in {path.name}.{hint}"

            count = content.count(find_text)
            new_content = content.replace(find_text, replace_text)
            path.write_text(new_content, encoding="utf-8")

            return f"Replaced {count} occurrence(s) in {path.name}. File saved."

        except Exception as e:
            return f"Edit failed: {e}"


class CommandRunnerTool(BaseTool):
    name: str = "run_command"
    description: str = (
        "Run a terminal command and return the output. Use this for: "
        "cargo build, go build, python -m pytest, pip install, etc. "
        "Input: the command to run. "
        "Commands run from the acumen project directory. "
        "Example: 'cargo build --release' or 'python -c \"print(1+1)\"'"
    )

    def _run(self, **kwargs: Any) -> str:
        command = ""
        for key, val in kwargs.items():
            if val and isinstance(val, str) and len(val.strip()) > 1:
                command = str(val).strip()
                break

        if not command:
            return "Provide a command to run."

        if not is_safe_command(command):
            logger.warning(f"BLOCKED unsafe command: {command}")
            return "Command blocked for safety reasons."

        logger.info(f"Running command: {command[:80]}")

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(Path.home() / "acumen"),
                env={**os.environ, "PYTHONPATH": str(Path.home() / "acumen")},
            )

            output = ""
            if result.stdout:
                output += f"STDOUT:\n{result.stdout[-2000:]}\n"
            if result.stderr:
                output += f"STDERR:\n{result.stderr[-2000:]}\n"
            if result.returncode != 0:
                output += f"\nEXIT CODE: {result.returncode} (error)"
            else:
                output += f"\nEXIT CODE: 0 (success)"

            if not output.strip():
                output = "Command completed with no output."

            return output

        except subprocess.TimeoutExpired:
            return "Command timed out after 120 seconds."
        except Exception as e:
            return f"Command failed: {e}"


class AutoFixTool(BaseTool):
    name: str = "auto_fix_code"
    description: str = (
        "Automatically try to fix code by running it, reading errors, and retrying. "
        "Input: a JSON with 'filepath' (the file to test) and 'test_command' "
        "(the command to verify it works). "
        "Example: {\"filepath\": \"acumen/tools/new_tool.py\", "
        "\"test_command\": \"python -c 'from acumen.tools.new_tool import MyTool; print(MyTool())'\"} "
        "The tool will run the test, and if it fails, return the error for you to fix."
    )

    def _run(self, **kwargs: Any) -> str:
        filepath = kwargs.get("filepath", kwargs.get("file", ""))
        test_command = kwargs.get("test_command", kwargs.get("command", kwargs.get("test", "")))

        if not filepath or not test_command:
            for key, val in kwargs.items():
                if isinstance(val, str):
                    if "/" in val or "\\" in val or val.endswith(".py"):
                        filepath = val
                    elif val.startswith("python") or val.startswith("cargo") or val.startswith("go"):
                        test_command = val

        if not filepath:
            return "Provide 'filepath' and 'test_command' parameters."

        if not test_command:
            # Default: try to import the file
            module = filepath.replace("/", ".").replace("\\", ".").replace(".py", "")
            test_command = f"python -c \"import {module}\""

        path = Path(filepath)
        if not path.is_absolute():
            path = Path.home() / "acumen" / filepath

        if not is_safe_path(str(path)):
            return f"Access denied: {path}"

        if not is_safe_command(test_command):
            return "Test command blocked for safety."

        # Run the test
        try:
            result = subprocess.run(
                test_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(Path.home() / "acumen"),
                env={**os.environ, "PYTHONPATH": str(Path.home() / "acumen")},
            )

            if result.returncode == 0:
                output = f"TEST PASSED!\n"
                if result.stdout:
                    output += f"Output: {result.stdout[:500]}\n"
                output += f"\nFile {path.name} is working correctly."
                return output
            else:
                # Parse the error
                error = result.stderr or result.stdout or "Unknown error"
                output = f"TEST FAILED\n\n"
                output += f"Command: {test_command}\n"
                output += f"Exit code: {result.returncode}\n\n"
                output += f"ERROR OUTPUT:\n{error[-1500:]}\n\n"

                # Try to extract actionable info
                error_info = self._parse_error(error, filepath)
                if error_info:
                    output += f"PARSED ERROR:\n{error_info}\n\n"

                output += (
                    "FIX INSTRUCTIONS: Read the error above, use file_edit to fix "
                    "the specific line, then run auto_fix_code again to verify. "
                    "If you cannot fix it, use claude_code_assist."
                )
                return output

        except subprocess.TimeoutExpired:
            return "Test timed out after 60 seconds."
        except Exception as e:
            return f"Test failed to run: {e}"

    def _parse_error(self, error_text, filepath):
        """Extract actionable info from error output."""
        info = []

        # Python errors
        py_match = re.findall(r'File "(.+?)", line (\d+).*?\n\s*(.+)', error_text)
        for match in py_match[-3:]:
            info.append(f"  File: {match[0]}, Line: {match[1]}, Code: {match[2]}")

        # Python exception
        exc_match = re.findall(r'(\w+Error: .+)', error_text)
        for match in exc_match[-2:]:
            info.append(f"  Exception: {match}")

        # Rust errors
        rust_match = re.findall(r'error\[E\d+\]: (.+)\n\s*--> (.+?):(\d+)', error_text)
        for match in rust_match[-3:]:
            info.append(f"  Rust Error: {match[0]}, File: {match[1]}, Line: {match[2]}")

        # Go errors
        go_match = re.findall(r'(.+\.go):(\d+):\d+: (.+)', error_text)
        for match in go_match[-3:]:
            info.append(f"  Go Error: {match[2]}, File: {match[0]}, Line: {match[1]}")

        return "\n".join(info) if info else None
