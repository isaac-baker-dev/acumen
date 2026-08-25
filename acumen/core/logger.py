"""
Acumen Logger - Local-only structured logging.

All logs stay on disk. No external endpoints.
"""

import json, logging
from datetime import datetime
from acumen.core.config import LOG_DIR, TELEMETRY_ENABLED

def get_logger(name: str, log_file: str = "acumen.log") -> logging.Logger:
    assert not TELEMETRY_ENABLED, "Telemetry must be disabled"

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(str(LOG_DIR / log_file))
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(JsonFormatter())
    logger.addHandler(fh)

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(sh)

    return logger

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "ts": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        })