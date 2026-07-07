from __future__ import annotations

import time
from typing import Any


class WorkingMemory:
    """Task-scoped ephemeral memory. Data expires after task completion or TTL."""

    def __init__(self, default_ttl: float = 300.0):
        self.default_ttl = default_ttl
        self._data: dict[str, dict[str, Any]] = {}
        self._timestamps: dict[str, dict[str, float]] = {}

    def set(self, key: str, value: Any, ttl: float | None = None, task_id: str = "") -> None:
        ns = self._namespace(task_id)
        ns[key] = value
        self._timestamps.setdefault(task_id, {})[key] = time.time()
        self._timestamps[task_id][f"{key}_ttl"] = ttl if ttl is not None else self.default_ttl

    def get(self, key: str, task_id: str = "", default: Any = None) -> Any:
        ns = self._namespace(task_id)
        if key not in ns:
            return default
        ts = self._timestamps.get(task_id, {}).get(key, 0)
        ttl = self._timestamps.get(task_id, {}).get(f"{key}_ttl", self.default_ttl)
        if time.time() - ts > ttl:
            del ns[key]
            return default
        return ns[key]

    def clear_task(self, task_id: str) -> None:
        self._data.pop(task_id, None)
        self._timestamps.pop(task_id, None)

    def clear_all(self) -> None:
        self._data.clear()
        self._timestamps.clear()

    def snapshot(self, task_id: str = "") -> dict[str, Any]:
        return dict(self._namespace(task_id))

    def _namespace(self, task_id: str) -> dict[str, Any]:
        return self._data.setdefault(task_id, {})
