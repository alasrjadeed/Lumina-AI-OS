"""Memory store with multi-thread conversation support."""

import json
import os
import uuid
from datetime import datetime

MEMORY_FILE = "lumina_memory.json"


class MemoryStore:
    def __init__(self, path: str = MEMORY_FILE):
        self.path = path
        self._data = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.path):
            with open(self.path) as f:
                return json.load(f)
        return {
            "conversations": [],
            "threads": [],
            "projects": [],
            "preferences": {},
            "learned_patterns": [],
        }

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self._data, f, indent=2)

    def add_conversation(self, role: str, content: str, thread_id: str | None = None):
        if thread_id:
            for t in self._data.get("threads", []):
                if t["id"] == thread_id:
                    t["messages"].append(
                        {
                            "role": role,
                            "content": content,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                    t["updated_at"] = datetime.now().isoformat()
                    self._save()
                    return
        self._data["conversations"].append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self._save()

    def get_recent_context(self, limit: int = 10, thread_id: str | None = None) -> str:
        if thread_id:
            for t in self._data.get("threads", []):
                if t["id"] == thread_id:
                    recent = t["messages"][-limit:]
                    return "\n".join(f"{c['role']}: {c['content'][:200]}" for c in recent)
        recent = self._data["conversations"][-limit:]
        return "\n".join(f"{c['role']}: {c['content'][:200]}" for c in recent)

    def get_conversations(self, limit: int = 10) -> list[dict]:
        return self._data["conversations"][-limit:]

    def create_thread(self, title: str = "New Chat") -> dict:
        thread = {
            "id": uuid.uuid4().hex[:12],
            "title": title,
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        self._data.setdefault("threads", []).insert(0, thread)
        self._save()
        return thread

    def list_threads(self, limit: int = 50) -> list[dict]:
        threads = self._data.get("threads", [])[:limit]
        return [
            {
                "id": t["id"],
                "title": t["title"],
                "message_count": len(t["messages"]),
                "created_at": t["created_at"],
                "updated_at": t["updated_at"],
            }
            for t in threads
        ]

    def get_thread(self, thread_id: str) -> dict | None:
        for t in self._data.get("threads", []):
            if t["id"] == thread_id:
                return t
        return None

    def delete_thread(self, thread_id: str) -> bool:
        threads = self._data.get("threads", [])
        for i, t in enumerate(threads):
            if t["id"] == thread_id:
                threads.pop(i)
                self._save()
                return True
        return False

    def rename_thread(self, thread_id: str, title: str) -> bool:
        for t in self._data.get("threads", []):
            if t["id"] == thread_id:
                t["title"] = title
                self._save()
                return True
        return False


memory = MemoryStore()
