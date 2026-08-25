# File: acumen/tools/file_ops.py
from pathlib import Path
from crewai.tools import BaseTool
from acumen.security.permissions import check_file_read, check_file_write
from acumen.security.audit import audit

class FileReadTool(BaseTool):
    name: str = "Read File"
    description: str = "Read a file. Input: file path."

    def _run(self, path: str) -> str:
        if not check_file_read(path): return f"ACCESS DENIED: {path}"
        try: return Path(path).read_text(encoding="utf-8",errors="replace")[:5000]
        except Exception as e: return f"Error: {e}"

class FileWriteTool(BaseTool):
    name: str = "Write File"
    description: str = "Write to file. Input: 'path|||content'."

    def _run(self, s: str) -> str:
        if "|||" not in s: return "Format: path|||content"
        path, content = s.split("|||", 1)
        if not check_file_write(path.strip()): return f"ACCESS DENIED"
        try:
            p = Path(path.strip()); p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return f"Wrote {len(content)} chars to {path.strip()}"
        except Exception as e: return f"Error: {e}"