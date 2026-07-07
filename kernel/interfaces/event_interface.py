from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IEvent(Protocol):
    name: str
    payload: Any
    timestamp: float
    source: str
    is_replay: bool
    correlation_id: str | None
    version: int
