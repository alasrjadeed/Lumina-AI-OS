from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

from kernel.events.event import Event
from kernel.events.middleware import EventMiddleware

if TYPE_CHECKING:
    from kernel.events.subscription import Subscription


@dataclass
class EventTypeMetrics:
    published: int = 0
    dispatched: int = 0
    failed: int = 0
    total_duration: float = 0.0

    @property
    def avg_duration(self) -> float:
        dispatched = self.dispatched or 1
        return self.total_duration / dispatched


class MetricsMiddleware(EventMiddleware):
    def __init__(self) -> None:
        self._per_type: dict[str, EventTypeMetrics] = defaultdict(EventTypeMetrics)
        self._timestamps: dict[str, float] = {}

    @property
    def per_type(self) -> dict[str, EventTypeMetrics]:
        return dict(self._per_type)

    def snapshot(self) -> dict:
        return {name: asdict(m) for name, m in self._per_type.items()}

    async def before_publish(self, event: Event) -> Event:
        self._timestamps[event.correlation_id or event.name] = time.time()
        return event

    async def after_publish(self, event: Event) -> None:
        self._per_type[event.name].published += 1

    async def before_dispatch(self, event: Event) -> Event:
        self._timestamps[event.correlation_id or event.name] = time.time()
        return event

    async def before_handler(
        self,
        subscription: Subscription,
        event: Event,
    ) -> Event:
        return event

    async def after_dispatch(self, event: Event) -> None:
        return

    async def after_handler(
        self,
        subscription: Subscription,
        event: Event,
    ) -> None:
        self._per_type[event.name].dispatched += 1
        key = event.correlation_id or event.name
        start = self._timestamps.pop(key, None)
        if start is not None:
            self._per_type[event.name].total_duration += time.time() - start

    async def on_exception(
        self,
        subscription: Subscription,
        event: Event,
        exception: Exception,
    ) -> None:
        self._per_type[event.name].failed += 1
