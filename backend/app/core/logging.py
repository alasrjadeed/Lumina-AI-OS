import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra"):
            log_entry["extra"] = record.extra
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def setup_logging(level: str = "INFO", log_dir: str = "logs"):
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)

    file_handler = logging.FileHandler(log_path / "lumina.log")
    file_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(file_handler)

    audit_handler = logging.FileHandler(log_path / "audit.log")
    audit_handler.setLevel(logging.WARNING)
    audit_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(audit_handler)

    return root_logger


def get_logger(name: str, extra: Dict[str, Any] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger = logging.LoggerAdapter(logger, extra or {})
    return logger
