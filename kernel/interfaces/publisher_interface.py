from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from kernel.events.event import Event


@runtime_checkable
class IPublisher(Protocol):
    async def publish(self, event: Event) -> None:
        ...
