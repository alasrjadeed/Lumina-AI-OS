from __future__ import annotations

from typing import TYPE_CHECKING

from kernel.events.event import Event
from kernel.events.middleware import BaseMiddleware
from kernel.log import setup_log

if TYPE_CHECKING:
    from kernel.events.subscription import Subscription

log = setup_log("events.middleware.logging")


class LoggingMiddleware(BaseMiddleware):
    def __init__(self, level: str = "info") -> None:
        self._level = level

    async def before_publish(self, event: Event) -> Event:
        self._log("Publishing event: %s (source=%s)", event.name, event.source)
        return event

    async def after_publish(self, event: Event) -> None:
        self._log("Published event: %s", event.name)

    async def before_dispatch(self, event: Event) -> Event:
        self._log("Dispatching event: %s", event.name)
        return event

    async def before_handler(
        self,
        subscription: Subscription,
        event: Event,
    ) -> Event:
        self._log(
            "Running handler for %s on topic=%s",
            event.name,
            subscription.topic,
        )
        return event

    async def after_handler(
        self,
        subscription: Subscription,
        event: Event,
    ) -> None:
        self._log(
            "Handler completed for %s on topic=%s",
            event.name,
            subscription.topic,
        )

    async def on_exception(
        self,
        subscription: Subscription,
        event: Event,
        exception: Exception,
    ) -> None:
        self._log(
            "Handler exception for %s on topic=%s: %s",
            event.name,
            subscription.topic,
            exception,
        )

    async def after_dispatch(self, event: Event) -> None:
        self._log("Dispatch complete: %s", event.name)

    def _log(self, fmt: str, *args: object) -> None:
        getattr(log, self._level)(fmt, *args)
