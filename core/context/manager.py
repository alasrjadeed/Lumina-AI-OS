from __future__ import annotations

from typing import Any


class ContextManager:
    """Manages conversation context window, sliding, summarization."""

    def __init__(self, max_tokens: int = 4096, reserve_tokens: int = 1024):
        self.max_tokens = max_tokens
        self.reserve_tokens = reserve_tokens
        self._messages: list[dict[str, str]] = []
        self._metadata: dict[str, Any] = {}

    def add(self, role: str, content: str, metadata: dict | None = None) -> None:
        msg: dict[str, str] = {"role": role, "content": content}
        self._messages.append(msg)
        self._trim()

    def add_message(self, msg: dict[str, str]) -> None:
        self._messages.append(msg)
        self._trim()

    def get_messages(self) -> list[dict[str, str]]:
        return list(self._messages)

    def last(self, n: int = 1) -> list[dict[str, str]]:
        return self._messages[-n:]

    def count(self) -> int:
        return len(self._messages)

    def clear(self) -> None:
        self._messages.clear()

    def set_metadata(self, key: str, value: Any) -> None:
        self._metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        return self._metadata.get(key, default)

    def window(self, start: int = 0, end: int | None = None) -> list[dict[str, str]]:
        return self._messages[start:end]

    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 2

    def _trim(self) -> None:
        budget = self.max_tokens - self.reserve_tokens
        while self._messages and self._total_tokens() > budget:
            self._messages.pop(0)

    def _total_tokens(self) -> int:
        return sum(self._estimate_tokens(m.get("content", "")) for m in self._messages)
