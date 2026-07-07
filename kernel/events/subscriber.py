from __future__ import annotations

from collections.abc import Awaitable, Callable

from kernel.events.event import Event

EventHandler = Callable[[Event], Awaitable[None]]


class Subscriber:
    """
    Wraps a handler with an optional identifier.

    Handlers now receive a single Event object.
    This adapter allows callers with the old (event_name, data)
    signature to work with the new EventBus.
    """

    def __init__(
        self,
        handler: EventHandler | Callable[..., Awaitable[None] | None],
        handler_id: str | None = None,
    ):
        self._handler = handler
        self._handler_id = handler_id or getattr(handler, "__name__", str(handler))

    @property
    def handler(self) -> EventHandler | Callable[..., Awaitable[None] | None]:
        return self._handler

    @property
    def handler_id(self) -> str:
        return self._handler_id

    async def handle(self, event: Event) -> None:
        result = self._handler(event)
        if result is not None:
            await result
