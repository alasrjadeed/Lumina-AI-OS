from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IServiceProvider(Protocol):
    def get_service(self, service_type: type) -> Any:
        ...


class IDisposable(ABC):
    @abstractmethod
    async def dispose(self) -> None:
        ...
