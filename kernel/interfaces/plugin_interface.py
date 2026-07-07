from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from kernel.events.subscription import Subscription


class IPlugin(ABC):
    @abstractmethod
    async def on_load(self, container: Any | None = None) -> None:
        pass

    @abstractmethod
    async def on_unload(self) -> None:
        pass

    async def on_enable(self) -> None:
        pass

    async def on_disable(self) -> None:
        pass

    async def on_install(self) -> None:
        pass

    async def on_uninstall(self) -> None:
        pass

    @property
    def subscriptions(self) -> list[Subscription]:
        return []
