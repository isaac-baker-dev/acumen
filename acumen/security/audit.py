"""Acumen Audit Logger - Immutable local audit trail."""

import json
from datetime import datetime
from acumen.core.config import LOG_DIR
from acumen.core.logger import get_logger

logger = get_logger("acumen.security.audit", "audit.log")

class AuditLogger:
    def __init__(self):
        self.log_dir = LOG_DIR

    def _log_file(self):
        return self.log_dir / f"audit_{datetime.now():%Y-%m-%d}.jsonl"

    def log_action(self, agent, action, tool, inp, out, status):
        entry = {"ts":datetime.now().isoformat(),"agent":agent,
                 "action":action,"tool":tool,"input":inp[:300],
                 "output":out[:300],"status":status}
        with open(self._log_file(), "a") as f:
            f.write(json.dumps(entry)+"\n")
        if status == "blocked":
            logger.warning(f"BLOCKED: {agent} -> {action}")

    def log_security_event(self, event, details, severity="HIGH"):
        entry = {"ts":datetime.now().isoformat(),"event":event,
                 "details":details[:500],"severity":severity}
        with open(self._log_file(), "a") as f:
            f.write(json.dumps(entry)+"\n")
        logger.warning(f"SECURITY [{severity}]: {event}")

audit = AuditLogger()