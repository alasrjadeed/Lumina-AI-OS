from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from kernel.interfaces import IEvent


@dataclass(frozen=True)
class Event(IEvent):
    name: str
    payload: Any = None
    source: str = ""
    is_replay: bool = False
    correlation_id: str | None = ""  # pyright: ignore[reportIncompatibleVariableOverride]
    version: int = 0
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Event name must be a non-empty string")
