from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

PRIORITY_ORDER = {"system": 3, "assistant": 2, "user": 1, "tool": 0}

@dataclass
class ShortTermEntry:
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def priority(self) -> int:
        return PRIORITY_ORDER.get(self.role, 0)


class ShortTermMemory:
    """Ring buffer for recent conversation context with priority retention."""

    def __init__(self, max_size: int = 50):
        self.max_size = max_size
        self._entries: list[ShortTermEntry] = []

    def add(
        self, role: str, content: str,
        metadata: dict[str, Any] | None = None,
    ) -> ShortTermEntry:
        entry = ShortTermEntry(role=role, content=content, metadata=metadata or {})
        self._entries.append(entry)
        if len(self._entries) > self.max_size:
            self._evict()
        return entry

    def get_recent(self, n: int = 10) -> list[ShortTermEntry]:
        return self._entries[-n:]

    def get_all(self) -> list[ShortTermEntry]:
        return list(self._entries)

    def search(self, query: str, limit: int = 5) -> list[ShortTermEntry]:
        tokens = [t for t in query.lower().split() if len(t) > 2]
        scored = []
        for e in self._entries:
            content = e.content.lower()
            if tokens:
                matches = sum(1 for t in tokens if t in content)
                if matches == 0:
                    continue
                score = matches / len(tokens) + len(e.content) / 10000.0
            else:
                if query.lower() not in content:
                    continue
                score = len(e.content) / 1000.0
            scored.append((score, e))
        scored.sort(key=lambda x: -x[0])
        return [e for _, e in scored[:limit]]

    def clear(self) -> None:
        self._entries.clear()

    def _evict(self) -> None:
        sorted_entries = sorted(self._entries, key=lambda e: (e.priority, e.timestamp))
        self._entries = sorted_entries[self.max_size // 4:]
        self._entries.sort(key=lambda e: e.timestamp)
