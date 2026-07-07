from __future__ import annotations

import glob
import json
import os
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)
    id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_user(self) -> bool:
        return self.role == "user"

    @property
    def is_assistant(self) -> bool:
        return self.role == "assistant"

    @property
    def is_system(self) -> bool:
        return self.role == "system"

    @property
    def formatted_time(self) -> str:
        return datetime.fromtimestamp(self.timestamp).strftime("%H:%M")


@dataclass
class ChatSession:
    id: str
    title: str = "New Chat"
    messages: list[ChatMessage] = field(default_factory=list)
    created: float = field(default_factory=time.time)
    model: str = "default"
    system_prompt: str = ""

    @property
    def message_count(self) -> int:
        return len(self.messages)

    @property
    def last_message(self) -> ChatMessage | None:
        return self.messages[-1] if self.messages else None


class ChatHistory:
    """Persistent chat history storage."""

    def __init__(self, storage_dir: str = ".lumina_chats"):
        self.storage_dir = storage_dir
        self._sessions: dict[str, ChatSession] = {}
        self._current_id: str = ""
        os.makedirs(storage_dir, exist_ok=True)

    def create_session(self, title: str = "New Chat", system_prompt: str = "") -> ChatSession:
        session = ChatSession(
            id=str(uuid.uuid4())[:8],
            title=title,
            system_prompt=system_prompt,
        )
        self._sessions[session.id] = session
        self._current_id = session.id
        self._save_session(session)
        return session

    def add_message(self, role: str, content: str, session_id: str = "") -> ChatMessage:
        sid = session_id or self._current_id
        session = self._sessions.get(sid)
        if not session:
            session = self.create_session()
            sid = session.id
        msg = ChatMessage(role=role, content=content)
        self._sessions[sid].messages.append(msg)
        self._save_session(self._sessions[sid])
        return msg

    def get_session(self, session_id: str) -> ChatSession | None:
        return self._sessions.get(session_id)

    def list_sessions(self, limit: int = 50) -> list[ChatSession]:
        sessions = sorted(
            self._sessions.values(),
            key=lambda s: s.created, reverse=True,
        )
        return sessions[:limit]

    def delete_session(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            path = self._session_path(session_id)
            if os.path.exists(path):
                os.remove(path)
            return True
        return False

    def switch_to(self, session_id: str) -> bool:
        if session_id in self._sessions:
            self._current_id = session_id
            return True
        return False

    def current_session(self) -> ChatSession | None:
        return self._sessions.get(self._current_id)

    def get_messages(self, session_id: str = "") -> list[ChatMessage]:
        sid = session_id or self._current_id
        session = self._sessions.get(sid)
        return list(session.messages) if session else []

    def search(self, query: str, session_id: str = "") -> list[ChatMessage]:
        q = query.lower()
        sessions = [session_id] if session_id else list(self._sessions.keys())
        results = []
        for sid in sessions:
            session = self._sessions.get(sid)
            if session:
                results.extend(
                    msg for msg in session.messages if q in msg.content.lower()
                )
        return results

    def clear_current(self) -> None:
        session = self.current_session()
        if session:
            session.messages.clear()
            self._save_session(session)

    def _session_path(self, session_id: str) -> str:
        return os.path.join(self.storage_dir, f"{session_id}.json")

    def _save_session(self, session: ChatSession) -> None:
        path = self._session_path(session.id)
        data = {
            "id": session.id,
            "title": session.title,
            "created": session.created,
            "model": session.model,
            "system_prompt": session.system_prompt,
            "messages": [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp}
                for m in session.messages
            ],
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def load_all(self) -> int:
        count = 0
        for path in glob.glob(os.path.join(self.storage_dir, "*.json")):
            try:
                with open(path) as f:
                    data = json.load(f)
                messages = [
                    ChatMessage(
                        role=m["role"], content=m["content"],
                        timestamp=m.get("timestamp", 0),
                    )
                    for m in data.get("messages", [])
                ]
                session = ChatSession(
                    id=data["id"],
                    title=data.get("title", "Chat"),
                    messages=messages,
                    created=data.get("created", 0),
                    model=data.get("model", "default"),
                    system_prompt=data.get("system_prompt", ""),
                )
                self._sessions[session.id] = session
                count += 1
            except Exception:
                pass
        return count


on_message: Callable[[ChatMessage], None] | None = None
