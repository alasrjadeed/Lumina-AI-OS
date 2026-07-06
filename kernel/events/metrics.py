"""
Lumina AI
Event Bus Metrics
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import UTC, datetime


@dataclass(slots=True)
class EventBusMetrics:
    published_events: int = 0
    dispatched_events: int = 0
    failed_events: int = 0
    retried_events: int = 0
    active_subscribers: int = 0
    queue_depth: int = 0

    started_at: datetime = datetime.now(UTC)

    @property
    def uptime_seconds(self) -> float:
        return (
            datetime.now(UTC) - self.started_at
        ).total_seconds()

    def snapshot(self) -> dict:
        return asdict(self)
