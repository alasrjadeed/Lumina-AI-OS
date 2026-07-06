from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable

from kernel.dependency.exceptions import DependencyError


class ServiceProvider(ABC):
    @abstractmethod
    def create_instance(
        self,
        container: Any,
        resolver: Any,
    ) -> Any:
        ...


class TypeProvider(ServiceProvider):
    def __init__(self, service_type: type) -> None:
        self._service_type = service_type

    @property
    def service_type(self) -> type:
        return self._service_type

    def create_instance(
        self,
        container: Any,
        resolver: Any,
    ) -> Any:
        return resolver.resolve_type(self._service_type, container)


class InstanceProvider(ServiceProvider):
    def __init__(self, instance: Any) -> None:
        self._instance = instance

    def create_instance(
        self,
        container: Any,
        resolver: Any,
    ) -> Any:
        return self._instance


class FactoryProvider(ServiceProvider):
    def __init__(self, factory: Callable[[Any], Any]) -> None:
        self._factory = factory

    def create_instance(
        self,
        container: Any,
        resolver: Any,
    ) -> Any:
        result = self._factory(container)
        if result is None:
            msg = "Factory returned None"
            raise DependencyError(msg)
        return result
