from __future__ import annotations

from kernel.dependency.container import DIContainer


class Scope:
    def __init__(self, parent: DIContainer) -> None:
        self._container = DIContainer()
        self._container._parent = parent
        self._container._registry = parent._registry
        self._container._resolver = parent._resolver
        self._container._singletons = parent._singletons
        self._parent = parent

    def resolve(self, service: str | type) -> object:
        return self._container.resolve(service)

    def try_resolve(self, service: str | type) -> object | None:
        return self._container.try_resolve(service)

    def dispose(self) -> None:
        self._container._scoped_instances.clear()
