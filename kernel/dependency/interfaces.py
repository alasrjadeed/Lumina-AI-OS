from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IServiceProvider(Protocol):
    def get_service(self, service_type: type) -> Any:
        ...


@runtime_checkable
class IDisposable(Protocol):
    def dispose(self) -> None:
        ...
