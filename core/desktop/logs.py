from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    def __ge__(self, other: LogLevel) -> bool:
        order = list(LogLevel)
        return order.index(self) >= order.index(other)


@dataclass
class LogEntry:
    level: LogLevel
    message: str
    source: str = ""
    timestamp: float = field(default_factory=time.time)
    traceback: str = ""

    @property
    def formatted_time(self) -> str:
        return datetime.fromtimestamp(self.timestamp).strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level.value,
            "message": self.message,
            "source": self.source,
            "timestamp": self.timestamp,
            "traceback": self.traceback,
        }


class LogManager:
    """Structured log storage with filtering, search, and export."""

    def __init__(self, max_entries: int = 10000, storage_path: str = ""):
        self.max_entries = max_entries
        self.storage_path = storage_path or "lumina_logs.json"
        self._entries: list[LogEntry] = []
        self._filters: list[Any] = []

    def log(
        self,
        level: LogLevel | str,
        message: str,
        source: str = "",
        traceback: str = "",
    ) -> LogEntry:
        if isinstance(level, str):
            level = LogLevel(level)
        entry = LogEntry(level=level, message=message, source=source, traceback=traceback)
        self._entries.append(entry)
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries :]
        return entry

    def debug(self, message: str, source: str = "") -> LogEntry:
        return self.log(LogLevel.DEBUG, message, source)

    def info(self, message: str, source: str = "") -> LogEntry:
        return self.log(LogLevel.INFO, message, source)

    def warning(self, message: str, source: str = "") -> LogEntry:
        return self.log(LogLevel.WARNING, message, source)

    def error(self, message: str, source: str = "", traceback: str = "") -> LogEntry:
        return self.log(LogLevel.ERROR, message, source, traceback)

    def critical(self, message: str, source: str = "", traceback: str = "") -> LogEntry:
        return self.log(LogLevel.CRITICAL, message, source, traceback)

    def get(
        self,
        level: LogLevel | str | None = None,
        source: str = "",
        limit: int = 100,
        offset: int = 0,
    ) -> list[LogEntry]:
        results = list(self._entries)
        if level:
            if isinstance(level, str):
                level = LogLevel(level)
            results = [e for e in results if e.level == level]
        if source:
            results = [e for e in results if source.lower() in e.source.lower()]
        results.reverse()
        return results[offset : offset + limit]

    def get_by_level(self, level: LogLevel | str, limit: int = 100) -> list[LogEntry]:
        return self.get(level=level, limit=limit)

    def search(self, query: str, limit: int = 100) -> list[LogEntry]:
        q = query.lower()
        results = [e for e in self._entries if q in e.message.lower() or q in e.source.lower()]
        results.reverse()
        return results[:limit]

    def get_errors(self, limit: int = 100) -> list[LogEntry]:
        return self.get_by_level(LogLevel.ERROR, limit) + self.get_by_level(
            LogLevel.CRITICAL, limit
        )

    def get_recent(self, limit: int = 50) -> list[LogEntry]:
        return list(reversed(self._entries[-limit:]))

    def count(self, level: LogLevel | str | None = None) -> int:
        if level:
            if isinstance(level, str):
                level = LogLevel(level)
            return sum(1 for e in self._entries if e.level == level)
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()

    def export_json(self, path: str = "", level: LogLevel | None = None) -> str:
        export_path = path or "log_export.json"
        entries = self.get(level=level, limit=self.max_entries) if level else self._entries
        data = [e.to_dict() for e in entries]
        with open(export_path, "w") as f:
            json.dump(data, f, indent=2)
        return export_path

    def export_text(self, path: str = "", level: LogLevel | None = None) -> str:
        export_path = path or "log_export.txt"
        entries = self.get(level=level, limit=self.max_entries) if level else self._entries
        lines = []
        for e in reversed(entries):
            lines.append(f"[{e.formatted_time}] [{e.level.value.upper()}] {e.message}")
            if e.traceback:
                lines.append(f"  {e.traceback}")
        with open(export_path, "w") as f:
            f.write("\n".join(lines))
        return export_path

    def save(self) -> None:
        data = [e.to_dict() for e in self._entries[-self.max_entries :]]
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self) -> int:
        if not os.path.exists(self.storage_path):
            return 0
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
            count = 0
            for d in data:
                entry = LogEntry(
                    level=LogLevel(d["level"]),
                    message=d["message"],
                    source=d.get("source", ""),
                    timestamp=d.get("timestamp", 0),
                    traceback=d.get("traceback", ""),
                )
                self._entries.append(entry)
                count += 1
            self._entries = self._entries[-self.max_entries :]
            return count
        except Exception:
            return 0
