from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

from kernel.dependency.exceptions import (
    CircularDependencyError,
    ServiceNotFoundError,
    ServiceRegistrationError,
)
from kernel.dependency.lifetime import Lifetime
from kernel.dependency.models import ServiceRegistration
from kernel.dependency.provider import (
    AliasProvider,
    DelegateProvider,
    FactoryProvider,
    InstanceProvider,
    ServiceProvider,
    TypeProvider,
)
from kernel.dependency.registry import ServiceRegistry
from kernel.dependency.resolver import Resolver


class DIContainer:
    def __init__(self) -> None:
        self._registry = ServiceRegistry()
        self._resolver = Resolver()
        self._singletons: dict[str | type, Any] = {}
        self._scoped_instances: dict[str | type, Any] = {}
        self._lock = threading.Lock()
        self._parent: DIContainer | None = None

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        service: str | type,
        *,
        instance: Any | None = None,
        factory: Callable[[Any], Any] | None = None,
        lifetime: Lifetime = Lifetime.TRANSIENT,
        tags: set[str] | None = None,
    ) -> None:
        provider: ServiceProvider
        if instance is not None:
            provider = InstanceProvider(instance)
        elif factory is not None:
            provider = FactoryProvider(factory)
        else:
            msg = "Must provide instance, factory, or use register_type()"
            raise ServiceRegistrationError(str(service), msg)

        self._registry.register(
            ServiceRegistration(
                service=service,
                provider=provider,
                lifetime=lifetime,
                tags=tags or set(),
            ),
        )

    def register_type(
        self,
        service: str | type,
        concrete: type | None = None,
        lifetime: Lifetime = Lifetime.TRANSIENT,
        tags: set[str] | None = None,
    ) -> None:
        concrete_type = concrete or service
        if not isinstance(concrete_type, type):
            msg = f"concrete must be a type, got {type(concrete_type)}"
            raise ServiceRegistrationError(str(service), msg)

        if isinstance(service, type):
            key: str | type = service
        else:
            key = service

        self._registry.register(
            ServiceRegistration(
                service=key,
                provider=TypeProvider(concrete_type),
                lifetime=lifetime,
                tags=tags or set(),
            ),
        )

    def register_instance(
        self,
        service: str | type,
        instance: Any,
        *,
        tags: set[str] | None = None,
    ) -> None:
        self._registry.register(
            ServiceRegistration(
                service=service,
                provider=InstanceProvider(instance),
                lifetime=Lifetime.SINGLETON,
                tags=tags or set(),
            ),
        )

    def register_factory(
        self,
        service: str | type,
        factory: Callable[[Any], Any],
        lifetime: Lifetime = Lifetime.TRANSIENT,
        *,
        tags: set[str] | None = None,
    ) -> None:
        self._registry.register(
            ServiceRegistration(
                service=service,
                provider=FactoryProvider(factory),
                lifetime=lifetime,
                tags=tags or set(),
            ),
        )

    def register_alias(
        self,
        service: str | type,
        target: str | type,
        *,
        tags: set[str] | None = None,
    ) -> None:
        self._registry.register(
            ServiceRegistration(
                service=service,
                provider=AliasProvider(target),
                lifetime=Lifetime.TRANSIENT,
                tags=tags or set(),
            ),
        )

    def register_delegate(
        self,
        service: str | type,
        factory: Callable[[Any, Any], Any],
        lifetime: Lifetime = Lifetime.TRANSIENT,
        *,
        tags: set[str] | None = None,
    ) -> None:
        self._registry.register(
            ServiceRegistration(
                service=service,
                provider=DelegateProvider(factory),
                lifetime=lifetime,
                tags=tags or set(),
            ),
        )

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def resolve(self, service: str | type) -> Any:
        registration = self._registry.get(service)
        if registration is not None:
            return self._get_from_registration(registration)

        if isinstance(service, type):
            return self._resolver.resolve_type(service, self)

        raise ServiceNotFoundError(str(service))

    def try_resolve(self, service: str | type) -> Any | None:
        try:
            return self.resolve(service)
        except (ServiceNotFoundError, CircularDependencyError):
            return None

    def resolve_name(self, name: str) -> Any:
        return self.resolve(name)

    def resolve_all(self) -> dict[str | type, Any]:
        return {reg.service: self.resolve(reg.service) for reg in self._registry.all()}

    def _get_from_registration(
        self,
        registration: ServiceRegistration,
    ) -> Any:
        lifetime = registration.lifetime

        if lifetime == Lifetime.SINGLETON:
            return self._resolve_singleton(registration)

        if lifetime == Lifetime.SCOPED:
            return self._resolve_scoped(registration)

        return registration.provider.create_instance(self, self._resolver)

    def _resolve_singleton(
        self,
        registration: ServiceRegistration,
    ) -> Any:
        key = registration.service
        with self._lock:
            if key in self._singletons:
                return self._singletons[key]

        instance = registration.provider.create_instance(self, self._resolver)

        with self._lock:
            if key not in self._singletons:
                self._singletons[key] = instance
            return self._singletons[key]

    def _resolve_scoped(
        self,
        registration: ServiceRegistration,
    ) -> Any:
        key = registration.service
        with self._lock:
            if key in self._scoped_instances:
                return self._scoped_instances[key]

        instance = registration.provider.create_instance(self, self._resolver)

        with self._lock:
            if key not in self._scoped_instances:
                self._scoped_instances[key] = instance
            return self._scoped_instances[key]

    # ------------------------------------------------------------------
    # Scopes
    # ------------------------------------------------------------------

    def create_scope(self) -> DIContainer:
        scope = DIContainer()
        scope._parent = self
        scope._registry = self._registry
        scope._resolver = self._resolver
        scope._singletons = self._singletons
        return scope

    def dispose_scope(self) -> None:
        """Alias for dispose(). Provided for backward compatibility."""
        self.dispose()

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_service(self, service_type: type) -> Any:
        return self.resolve(service_type)

    def has(self, service: str | type) -> bool:
        return self._registry.has(service)

    def clear(self) -> None:
        with self._lock:
            self._registry.clear()
            self._singletons.clear()
            self._scoped_instances.clear()

    def registered(self) -> list[str]:
        return [str(r.service) for r in self._registry.all()]

    def is_registered(self, service: str | type) -> bool:
        return self._registry.has(service)

    def remove(self, service: str | type) -> bool:
        return self._registry.remove(service)

    def dispose(self) -> None:
        self._scoped_instances.clear()
