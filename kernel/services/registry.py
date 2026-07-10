from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, TypeVar

from kernel.dependency import DIContainer
from kernel.dependency.exceptions import ServiceNotFoundError as NewServiceNotFoundError
from kernel.dependency.lifetime import Lifetime
from kernel.events import Event
from kernel.exceptions import (
    CircularDependencyError,
    ServiceLifecycleError,
    ServiceNotFoundError,
)
from kernel.interfaces import IService
from kernel.log import setup_log
from kernel.services.models import (
    HealthChecker,
    HealthStatus,
    ServiceRecord,
    ServiceStatus,
)

T = TypeVar("T")

log = setup_log("services")


class ServiceRegistry:
    def __init__(self, container: DIContainer | None = None):
        self._di = container or DIContainer()
        self._records: dict[str, ServiceRecord] = {}
        self._event_bus: Any = None
        if container is not None:
            self._event_bus = container.try_resolve("event_bus")

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        name: str,
        instance: Any,
        tags: set[str] | None = None,
        dependencies: list[str] | None = None,
    ) -> ServiceRecord:
        self._di.register_instance(name, instance)
        record = ServiceRecord(
            name=name,
            instance=instance,
            tags=tags or set(),
            dependencies=dependencies or [],
        )
        self._records[name] = record
        self._emit("service.registered", name)
        log.info("Registered service: %s", name)
        return record

    def register_factory(
        self,
        name: str,
        factory: Callable[..., Any],
        lifetime: Lifetime = Lifetime.TRANSIENT,
        tags: set[str] | None = None,
        dependencies: list[str] | None = None,
    ) -> ServiceRecord:
        self._di.register_factory(name, lambda c: factory(c), lifetime=lifetime)
        record = ServiceRecord(
            name=name,
            instance=None,
            tags=tags or set(),
            dependencies=dependencies or [],
        )
        self._records[name] = record
        self._emit("service.registered", name)
        log.info("Registered factory: %s", name)
        return record

    def register_type(
        self,
        name: str,
        type_: type,
        lifetime: Lifetime = Lifetime.TRANSIENT,
        tags: set[str] | None = None,
        dependencies: list[str] | None = None,
    ) -> ServiceRecord:
        self._di.register_type(name, type_, lifetime=lifetime)
        record = ServiceRecord(
            name=name,
            instance=None,
            tags=tags or set(),
            dependencies=dependencies or [],
        )
        self._records[name] = record
        self._emit("service.registered", name)
        log.info("Registered type: %s", name)
        return record

    def register_many(
        self,
        services: dict[str, Any],
        tags: dict[str, set[str]] | None = None,
        dependencies: dict[str, list[str]] | None = None,
    ) -> list[ServiceRecord]:
        records: list[ServiceRecord] = []
        for name, instance in services.items():
            record = self.register(
                name,
                instance,
                tags=(tags or {}).get(name),
                dependencies=(dependencies or {}).get(name),
            )
            records.append(record)
        return records

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def resolve(self, name: str) -> Any:
        try:
            return self._di.resolve(name)
        except NewServiceNotFoundError as e:
            raise ServiceNotFoundError(name) from e

    def try_resolve(self, name: str) -> Any | None:
        try:
            return self._di.resolve(name)
        except (NewServiceNotFoundError, ServiceNotFoundError):
            return None

    def get(self, name: str, default: Any = None) -> Any | None:
        try:
            return self.resolve(name)
        except ServiceNotFoundError:
            return default

    def has(self, name: str) -> bool:
        return name in self._records

    def count(self) -> int:
        return len(self._records)

    def list(self) -> list[str]:
        return list(self._records.keys())

    # ------------------------------------------------------------------
    # Removal
    # ------------------------------------------------------------------

    def remove(self, name: str) -> None:
        record = self._get_record(name)
        if record.status in (ServiceStatus.RUNNING, ServiceStatus.STARTING):
            raise ServiceLifecycleError(
                name, f"Cannot remove service in state '{record.status.value}'"
            )
        if not self._di.remove(name):
            raise ServiceNotFoundError(name)
        del self._records[name]
        self._emit("service.removed", name)
        log.info("Removed service: %s", name)

    def remove_many(self, names: list[str]) -> None:
        for name in names:
            self.remove(name)

    def clear(self) -> None:
        for record in list(self._records.values()):
            if record.status in (ServiceStatus.RUNNING, ServiceStatus.STARTING):
                raise ServiceLifecycleError(
                    record.name,
                    f"Cannot clear while service is '{record.status.value}'",
                )
        self._records.clear()
        log.info("Cleared all services")

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

    def tag(self, name: str, tags: set[str]) -> None:
        record = self._get_record(name)
        record.tags.update(tags)

    def untag(self, name: str, tags: set[str]) -> None:
        record = self._get_record(name)
        record.tags.difference_update(tags)

    def get_tags(self, name: str) -> set[str]:
        record = self._get_record(name)
        return record.tags.copy()

    def find_by_tag(self, tag: str) -> list[str]:
        return [n for n, r in self._records.items() if tag in r.tags]

    def list_by_tags(self, tags: set[str]) -> list[str]:
        return [n for n, r in self._records.items() if tags.issubset(r.tags)]

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def find_by_status(self, status: ServiceStatus) -> list[str]:
        return [n for n, r in self._records.items() if r.status is status]

    def find_by_type(self, type_: type) -> list[str]:
        results: list[str] = []
        for name, record in self._records.items():
            instance = record.instance
            if instance is None:
                try:
                    instance = self._di.resolve(name)
                except Exception:
                    continue
            if isinstance(instance, type_):
                results.append(name)
        return results

    def find_by_dependency(self, dependency_name: str) -> list[str]:
        return [n for n, r in self._records.items() if dependency_name in r.dependencies]

    def get_record(self, name: str) -> ServiceRecord | None:
        return self._records.get(name)

    # ------------------------------------------------------------------
    # Health checks
    # ------------------------------------------------------------------

    def add_health_check(
        self,
        name: str,
        checker: HealthChecker,
    ) -> None:
        record = self._get_record(name)
        record.health_checkers.append(checker)

    def remove_health_check(
        self,
        name: str,
        checker: HealthChecker,
    ) -> bool:
        record = self._get_record(name)
        try:
            record.health_checkers.remove(checker)
            return True
        except ValueError:
            return False

    def health(self, name: str) -> HealthStatus | None:
        record = self._get_record(name)
        if not record.health_checkers:
            return None

        overall: HealthStatus | None = None
        for checker in record.health_checkers:
            try:
                result = checker()
                if result is None:
                    continue
                if result is HealthStatus.UNHEALTHY:
                    overall = HealthStatus.UNHEALTHY
                elif result is HealthStatus.DEGRADED and overall is not HealthStatus.UNHEALTHY:
                    overall = HealthStatus.DEGRADED
                elif overall is None:
                    overall = HealthStatus.HEALTHY
            except Exception:
                overall = HealthStatus.UNHEALTHY

        record.health = overall
        record.last_health_check = datetime.now(UTC)
        return overall

    def health_all(self) -> dict[str, HealthStatus | None]:
        return {name: self.health(name) for name in self._records}

    # ------------------------------------------------------------------
    # Lifecycle: startup / shutdown
    # ------------------------------------------------------------------

    async def start(self, name: str) -> None:
        record = self._get_record(name)
        if record.status is ServiceStatus.RUNNING:
            return

        allowed = {ServiceStatus.CREATED, ServiceStatus.STOPPED, ServiceStatus.FAILED}
        if record.status not in allowed:
            raise ServiceLifecycleError(
                name,
                f"Cannot start from state '{record.status.value}'",
            )

        # Start dependencies first
        await self._start_dependencies(record)

        record.status = ServiceStatus.STARTING
        self._emit("service.starting", name)

        instance = self._resolve_instance(record)
        record.instance = instance

        if isinstance(instance, IService):
            try:
                await instance.initialize()
            except Exception as e:
                record.status = ServiceStatus.FAILED
                record.error = str(e)
                self._emit("service.failed", name)
                raise ServiceLifecycleError(name, f"Initialize failed: {e}") from e

        record.status = ServiceStatus.RUNNING
        record.started_at = datetime.now(UTC)
        self._emit("service.started", name)
        log.info("Started service: %s", name)

    async def stop(self, name: str) -> None:
        record = self._get_record(name)
        if record.status is ServiceStatus.STOPPED:
            return

        if record.status is not ServiceStatus.RUNNING:
            raise ServiceLifecycleError(
                name,
                f"Cannot stop from state '{record.status.value}'",
            )

        # Stop dependents first
        await self._stop_dependents(record)

        record.status = ServiceStatus.STOPPING
        self._emit("service.stopping", name)

        instance = self._resolve_instance(record)
        if isinstance(instance, IService):
            try:
                await instance.shutdown()
            except Exception as e:
                record.status = ServiceStatus.FAILED
                record.error = str(e)
                self._emit("service.failed", name)
                raise ServiceLifecycleError(name, f"Shutdown failed: {e}") from e

        record.status = ServiceStatus.STOPPED
        record.stopped_at = datetime.now(UTC)
        self._emit("service.stopped", name)
        log.info("Stopped service: %s", name)

    async def start_all(self) -> None:
        order = self._dependency_order()
        for name in order:
            record = self._records.get(name)
            if record and record.status is ServiceStatus.CREATED:
                await self.start(name)

    async def stop_all(self) -> None:
        order = self._dependency_order()
        for name in reversed(order):
            record = self._records.get(name)
            if record and record.status is ServiceStatus.RUNNING:
                await self.stop(name)

    # ------------------------------------------------------------------
    # Dependency ordering (topological sort)
    # ------------------------------------------------------------------

    def _dependency_order(self) -> list[str]:
        visited: set[str] = set()
        result: list[str] = []

        def visit(name: str, path: list[str]) -> None:
            if name in path:
                cycle = path[path.index(name) :] + [name]
                raise CircularDependencyError(cycle)
            if name in visited:
                return
            path.append(name)
            visited.add(name)
            record = self._records.get(name)
            if record:
                for dep in record.dependencies:
                    visit(dep, path)
            path.pop()
            result.append(name)

        for name in self._records:
            if name not in visited:
                visit(name, [])
        return result

    async def _start_dependencies(self, record: ServiceRecord) -> None:
        for dep in record.dependencies:
            dep_record = self._records.get(dep)
            if dep_record and dep_record.status is not ServiceStatus.RUNNING:
                await self.start(dep)

    async def _stop_dependents(self, record: ServiceRecord) -> None:
        for name, r in self._records.items():
            if record.name in r.dependencies and r.status is ServiceStatus.RUNNING:
                await self.stop(name)

    def _get_record(self, name: str) -> ServiceRecord:
        record = self._records.get(name)
        if not record:
            raise ServiceNotFoundError(name)
        return record

    def _resolve_instance(self, record: ServiceRecord) -> Any:
        if record.instance is not None:
            return record.instance
        try:
            instance = self._di.resolve(record.name)
            record.instance = instance
            return instance
        except NewServiceNotFoundError as e:
            raise ServiceNotFoundError(record.name) from e

    # ------------------------------------------------------------------
    # Event emission
    # ------------------------------------------------------------------

    def _emit(self, event_name: str, service_name: str) -> None:
        if self._event_bus is None:
            return
        with contextlib.suppress(Exception):
            asyncio.ensure_future(
                self._event_bus.publish(
                    Event(
                        name=f"service.{event_name}",
                        payload={"service": service_name},
                        source="services",
                    ),
                ),
            )
