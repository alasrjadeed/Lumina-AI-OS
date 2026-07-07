from __future__ import annotations

from typing import Protocol

from kernel.events.dead_letter import DeadLetterEntry


class DLQBackend(Protocol):
    def add(self, entry: DeadLetterEntry) -> None:
        ...

    def count(self) -> int:
        ...

    def latest(self, limit: int = 10) -> list[DeadLetterEntry]:
        ...

    def clear(self) -> None:
        ...

    def all(self) -> list[DeadLetterEntry]:
        ...
