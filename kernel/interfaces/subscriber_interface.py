from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from kernel.events.event import Event


@runtime_checkable
class ISubscriber(Protocol):
    @property
    def handler_id(self) -> str:
        ...

    async def handle(self, event: Event) -> None:
        ...
