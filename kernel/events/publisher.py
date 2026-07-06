from __future__ import annotations

from kernel.events.event import Event
from kernel.events.event_bus import EventBus


class Publisher:
    """
    Wraps an EventBus to expose only publish().

    This adapter lets callers publish without access to
    register/unregister/dispatch.
    """

    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus

    async def publish(self, event: Event) -> None:
        await self._event_bus.publish(event)
