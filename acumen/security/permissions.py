"""Acumen Permissions - Default-deny file and command access."""

from pathlib import Path
from acumen.core.config import ALLOWED_READ_DIRS, ALLOWED_WRITE_DIRS, BLOCKED_COMMANDS
from acumen.core.logger import get_logger

logger = get_logger("acumen.security", "security.log")

def check_file_read(path: str) -> bool:
    resolved = str(Path(path).resolve())
    for a in ALLOWED_READ_DIRS:
        if resolved.startswith(str(Path(a).resolve())):
            return True
    logger.warning(f"BLOCKED read: {path}")
    return False

def check_file_write(path: str) -> bool:
    resolved = str(Path(path).resolve())
    for a in ALLOWED_WRITE_DIRS:
        if resolved.startswith(str(Path(a).resolve())):
            return True
    logger.warning(f"BLOCKED write: {path}")
    return False

def check_command(cmd: str) -> bool:
    for b in BLOCKED_COMMANDS:
        if b in cmd.lower():
            logger.warning(f"BLOCKED command: {cmd}")
            return False
    return True

def sanitize_input(text: str) -> str:
    patterns = ["ignore previous instructions","ignore all previous",
                "disregard your","you are now","override your","system prompt:"]
    for pat in patterns:
        if pat.lower() in text.lower():
            logger.warning(f"Prompt injection detected: '{pat}'")
    return text