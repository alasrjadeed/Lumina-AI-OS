from typing import Any, Callable, TypeVar

from kernel.dependency import DIContainer
from kernel.dependency.exceptions import ServiceNotFoundError as NewServiceNotFoundError
from kernel.dependency.lifetime import Lifetime
from kernel.exceptions import ServiceNotFoundError
from kernel.log import setup_log

T = TypeVar("T")

log = setup_log("services")


class ServiceRegistry:
    def __init__(self, container: DIContainer | None = None):
        self._di = container or DIContainer()

    def register(self, name: str, instance: Any, dependencies: list[str] | None = None) -> None:
        self._di.register_instance(name, instance)
        log.info("Registered service: %s", name)

    def register_factory(
        self,
        name: str,
        factory: Callable[[Any], Any],
        dependencies: list[str] | None = None,
    ) -> None:
        self._di.register_factory(name, lambda c: factory(), lifetime=Lifetime.TRANSIENT)
        log.info("Registered factory: %s", name)

    def resolve(self, name: str) -> Any:
        try:
            return self._di.resolve(name)
        except NewServiceNotFoundError as e:
            raise ServiceNotFoundError(name) from e

    def get(self, name: str, default: Any = None) -> Any | None:
        try:
            return self.resolve(name)
        except ServiceNotFoundError:
            return default

    def has(self, name: str) -> bool:
        return self._di.is_registered(name)

    def remove(self, name: str) -> None:
        self._di._registry.remove(name)

    def list(self) -> list[str]:
        return [str(k) for k in self._di._registry.keys()]
