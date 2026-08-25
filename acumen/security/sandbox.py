"""Acumen Sandbox - Docker-isolated code execution."""

import subprocess, tempfile
from pathlib import Path
from acumen.core.config import SANDBOX_TIMEOUT, SANDBOX_MAX_MEM
from acumen.core.logger import get_logger
from acumen.security.audit import audit

logger = get_logger("acumen.security.sandbox")

def run_code_sandboxed(code: str, language: str = "python") -> dict:
    if language != "python":
        return {"stdout":"","stderr":f"Unsupported: {language}","exit_code":1,"timed_out":False}

    with tempfile.NamedTemporaryFile(mode="w",suffix=".py",delete=False) as f:
        f.write(code); code_path = f.name

    try:
        result = subprocess.run([
            "docker","run","--rm","--network=none",
            f"--memory={SANDBOX_MAX_MEM}","--cpus=1",
            "--read-only","--tmpfs","/tmp:size=64m",
            "--user","1000:1000","--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "-v",f"{code_path}:/code.py:ro",
            "acumen-sandbox:latest","python","/code.py"
        ], capture_output=True, text=True, timeout=SANDBOX_TIMEOUT)

        audit.log_action("system","code_exec","sandbox",code[:300],
                         (result.stdout+result.stderr)[:300],
                         "success" if result.returncode==0 else "error")

        return {"stdout":result.stdout,"stderr":result.stderr,
                "exit_code":result.returncode,"timed_out":False}

    except subprocess.TimeoutExpired:
        audit.log_security_event("timeout",f"Code exceeded {SANDBOX_TIMEOUT}s")
        return {"stdout":"","stderr":f"TIMEOUT ({SANDBOX_TIMEOUT}s)","exit_code":-1,"timed_out":True}

    finally:
        Path(code_path).unlink(missing_ok=True)