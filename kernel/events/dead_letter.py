from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from kernel.events.event import Event


@dataclass(slots=True)
class DeadLetterEntry:
    id: UUID = field(default_factory=uuid4)
    event: Event | None = None
    failed_at: datetime = field(
        default_factory=lambda: datetime.now(UTC),
    )
    attempts: int = 0
    exception: str = ""
    exception_type: str = ""
    subscriber: str = ""


class DeadLetterQueue:
    def __init__(self, max_entries: int = 5000) -> None:
        self._entries: deque[DeadLetterEntry] = deque(maxlen=max_entries)

    def add(self, entry: DeadLetterEntry) -> None:
        self._entries.append(entry)

    def count(self) -> int:
        return len(self._entries)

    def latest(self, limit: int = 10) -> list[DeadLetterEntry]:
        return list(self._entries)[-limit:]

    def clear(self) -> None:
        self._entries.clear()

    def all(self) -> list[DeadLetterEntry]:
        return list(self._entries)
