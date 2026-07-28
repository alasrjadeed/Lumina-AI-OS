from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any

_MEM_DIR = os.path.expanduser("~/.lumina/agent_memory")


class AgentMemoryStore:
    def __init__(self):
        self._memories: dict[str, list[dict]] = {}
        self._load()

    def _path(self, name: str) -> str:
        os.makedirs(_MEM_DIR, exist_ok=True)
        return os.path.join(_MEM_DIR, name)

    def _load(self) -> None:
        path = self._path("memories.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    self._memories = json.load(f)
            except Exception:
                self._memories = {}

    def _save(self) -> None:
        with open(self._path("memories.json"), "w") as f:
            json.dump(self._memories, f, indent=2)

    def list_agents(self) -> list[str]:
        return list(self._memories.keys())

    def get_memory(self, agent_id: str) -> list[dict]:
        return self._memories.get(agent_id, [])

    def add_memory(self, agent_id: str, key: str, value: Any, ttl: int | None = None) -> dict:
        entry = {
            "id": uuid.uuid4().hex[:8],
            "key": key,
            "value": value,
            "timestamp": time.time(),
            "ttl": ttl,
        }
        if agent_id not in self._memories:
            self._memories[agent_id] = []
        self._memories[agent_id].append(entry)
        self._save()
        return entry

    def update_memory(self, agent_id: str, entry_id: str, value: Any) -> dict | None:
        for entry in self._memories.get(agent_id, []):
            if entry["id"] == entry_id:
                entry["value"] = value
                entry["timestamp"] = time.time()
                self._save()
                return entry
        return None

    def delete_memory(self, agent_id: str, entry_id: str) -> bool:
        for i, entry in enumerate(self._memories.get(agent_id, [])):
            if entry["id"] == entry_id:
                self._memories[agent_id].pop(i)
                self._save()
                return True
        return False

    def clear_agent(self, agent_id: str) -> bool:
        if agent_id in self._memories:
            self._memories[agent_id] = []
            self._save()
            return True
        return False

    def get_stats(self) -> dict:
        return {
            "total_agents": len(self._memories),
            "total_entries": sum(len(v) for v in self._memories.values()),
            "agents": {k: len(v) for k, v in self._memories.items()},
        }


agent_memory_store = AgentMemoryStore()
