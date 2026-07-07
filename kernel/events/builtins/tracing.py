from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from kernel.events.event import Event
from kernel.events.middleware import BaseMiddleware

if TYPE_CHECKING:
    from kernel.events.subscription import Subscription


class TracingMiddleware(BaseMiddleware):
    def __init__(self, propagate: bool = True) -> None:
        self._propagate = propagate

    async def before_publish(self, event: Event) -> Event:
        if not event.correlation_id:
            event = Event(
                name=event.name,
                payload=event.payload,
                source=event.source,
                correlation_id=str(uuid.uuid4()),
                version=event.version,
                is_replay=event.is_replay,
                timestamp=event.timestamp,
            )
        return event

    async def before_handler(
        self,
        subscription: Subscription,
        event: Event,
    ) -> Event:
        if self._propagate and event.correlation_id:
            return Event(
                name=event.name,
                payload=event.payload,
                source=event.source,
                correlation_id=event.correlation_id,
                version=event.version,
                is_replay=event.is_replay,
                timestamp=event.timestamp,
            )
        return event
