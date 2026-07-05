import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, Generic, Optional, Set, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ServiceStatus(Enum):
    REGISTERED = auto()
    INITIALIZING = auto()
    RUNNING = auto()
    DEGRADED = auto()
    STOPPED = auto()
    ERROR = auto()


@dataclass
class ServiceDefinition(Generic[T]):
    name: str
    service_class: Type[T]
    instance: Optional[T] = None
    status: ServiceStatus = ServiceStatus.REGISTERED
    dependencies: Set[str] = field(default_factory=set)
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    registered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    error_count: int = 0
    health_check_func: Optional[callable] = None


class ServiceRegistry:
    def __init__(self):
        self._services: Dict[str, ServiceDefinition] = {}
        self._order: list[str] = []

    def register(
        self,
        name: str,
        service_class: Type[T],
        dependencies: Optional[set[str]] = None,
        version: str = "1.0.0",
        metadata: Optional[Dict[str, Any]] = None,
        health_check_func: Optional[callable] = None,
    ) -> ServiceDefinition[T]:
        if name in self._services:
            raise ValueError(f"Service '{name}' already registered")
        definition = ServiceDefinition(
            name=name,
            service_class=service_class,
            dependencies=dependencies or set(),
            version=version,
            metadata=metadata or {},
            health_check_func=health_check_func,
        )
        self._services[name] = definition
        self._order.append(name)
        logger.info(f"Service '{name}' registered (v{version})")
        return definition

    def unregister(self, name: str) -> bool:
        if name not in self._services:
            return False
        del self._services[name]
        self._order.remove(name)
        logger.info(f"Service '{name}' unregistered")
        return True

    def get(self, name: str) -> Optional[ServiceDefinition]:
        return self._services.get(name)

    def get_instance(self, name: str) -> Optional[T]:
        svc = self._services.get(name)
        if svc and svc.status == ServiceStatus.RUNNING:
            return svc.instance
        return None

    def set_instance(self, name: str, instance: T) -> None:
        svc = self._services.get(name)
        if svc:
            svc.instance = instance

    def resolve_dependency_order(self) -> list[str]:
        visited: set[str] = set()
        resolved: list[str] = []

        def visit(name: str, path: set[str]) -> None:
            if name in path:
                raise ValueError(f"Circular dependency detected: {' -> '.join(path | {name})}")
            if name in visited:
                return
            path.add(name)
            svc = self._services.get(name)
            if svc:
                for dep in svc.dependencies:
                    visit(dep, path)
            path.remove(name)
            visited.add(name)
            resolved.append(name)

        for name in self._order:
            visit(name, set())
        return resolved

    def get_status(self, name: str) -> Optional[ServiceStatus]:
        svc = self._services.get(name)
        return svc.status if svc else None

    def set_status(self, name: str, status: ServiceStatus) -> None:
        svc = self._services.get(name)
        if svc:
            svc.status = status
            if status == ServiceStatus.RUNNING:
                svc.started_at = datetime.now(timezone.utc)

    def all_services(self) -> Dict[str, ServiceDefinition]:
        return dict(self._services)

    def list_by_status(self, status: ServiceStatus) -> list[ServiceDefinition]:
        return [svc for svc in self._services.values() if svc.status == status]

    def get_service_count(self) -> int:
        return len(self._services)
