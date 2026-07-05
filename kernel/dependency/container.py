import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, Optional, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Lifetime(Enum):
    SINGLETON = auto()
    SCOPED = auto()
    TRANSIENT = auto()


@dataclass
class Registration:
    name: str
    factory: Callable[..., Any]
    lifetime: Lifetime
    instance: Optional[Any] = None
    resolved: bool = False


class DIContainer:
    def __init__(self):
        self._registrations: Dict[str, Registration] = {}
        self._scoped_instances: Dict[str, Any] = {}
        self._parent: Optional["DIContainer"] = None

    def register(
        self,
        name: str,
        factory: Callable[..., T],
        lifetime: Lifetime = Lifetime.SINGLETON,
    ) -> None:
        self._registrations[name] = Registration(
            name=name,
            factory=factory,
            lifetime=lifetime,
        )
        logger.debug(f"Registered DI: {name} ({lifetime.name})")

    def register_instance(self, name: str, instance: Any) -> None:
        self._registrations[name] = Registration(
            name=name,
            factory=lambda: instance,
            lifetime=Lifetime.SINGLETON,
            instance=instance,
            resolved=True,
        )

    def _resolve_internal(self, name: str, scoped_store: Dict[str, Any]) -> Any:
        reg = self._registrations.get(name)
        if not reg:
            if self._parent:
                return self._parent._resolve_internal(name, scoped_store)
            raise KeyError(f"No registration found for '{name}'")

        if reg.lifetime == Lifetime.SINGLETON:
            if not reg.resolved:
                reg.instance = reg.factory()
                reg.resolved = True
            return reg.instance

        if reg.lifetime == Lifetime.SCOPED:
            if name not in scoped_store:
                scoped_store[name] = reg.factory()
            return scoped_store[name]

        return reg.factory()

    def resolve(self, name: str) -> Any:
        return self._resolve_internal(name, self._scoped_instances)

    def create_scope(self) -> "DIContainer":
        scope = DIContainer()
        scope._parent = self
        return scope

    def clear_scope(self) -> None:
        self._scoped_instances.clear()

    def has(self, name: str) -> bool:
        if name in self._registrations:
            return True
        if self._parent:
            return self._parent.has(name)
        return False

    def remove(self, name: str) -> bool:
        return self._registrations.pop(name, None) is not None

    def clear(self) -> None:
        self._registrations.clear()
        self._scoped_instances.clear()
