from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from kernel.events.event import Event

if TYPE_CHECKING:
    from kernel.events.subscription import Subscription


@runtime_checkable
class EventMiddleware(Protocol):
    async def before_publish(self, event: Event) -> Event:
        ...

    async def after_publish(self, event: Event) -> None:
        ...

    async def before_dispatch(self, event: Event) -> Event:
        ...

    async def before_handler(
        self,
        subscription: Subscription,
        event: Event,
    ) -> Event:
        ...

    async def after_handler(
        self,
        subscription: Subscription,
        event: Event,
    ) -> None:
        ...

    async def on_exception(
        self,
        subscription: Subscription,
        event: Event,
        exception: Exception,
    ) -> None:
        ...

    async def after_dispatch(self, event: Event) -> None:
        ...


class BaseMiddleware(ABC):
    async def before_publish(self, event: Event) -> Event:
        return event

    async def after_publish(self, event: Event) -> None:
        return

    async def before_dispatch(self, event: Event) -> Event:
        return event

    async def before_handler(
        self,
        subscription: Subscription,
        event: Event,
    ) -> Event:
        return event

    async def after_handler(
        self,
        subscription: Subscription,
        event: Event,
    ) -> None:
        return

    async def on_exception(
        self,
        subscription: Subscription,
        event: Event,
        exception: Exception,
    ) -> None:
        return

    async def after_dispatch(self, event: Event) -> None:
        return
