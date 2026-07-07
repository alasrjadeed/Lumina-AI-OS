from __future__ import annotations

from threading import Lock

from kernel.dependency.exceptions import ServiceRegistrationError
from kernel.dependency.lifetime import Lifetime
from kernel.dependency.models import ServiceRegistration


class ServiceRegistry:
    def __init__(self) -> None:
        self._entries: dict[str | type, ServiceRegistration] = {}
        self._lock = Lock()

    def register(
        self,
        registration: ServiceRegistration,
    ) -> None:
        with self._lock:
            key = registration.service
            if key in self._entries:
                raise ServiceRegistrationError(
                    str(key),
                    "already registered",
                )
            self._entries[key] = registration

    def register_or_replace(
        self,
        registration: ServiceRegistration,
    ) -> bool:
        with self._lock:
            key = registration.service
            existed = key in self._entries
            self._entries[key] = registration
            return existed

    def bulk_register(
        self,
        registrations: list[ServiceRegistration],
    ) -> None:
        with self._lock:
            for reg in registrations:
                key = reg.service
                if key in self._entries:
                    raise ServiceRegistrationError(
                        str(key),
                        "already registered",
                    )
                self._entries[key] = reg

    def get(
        self,
        service: str | type,
    ) -> ServiceRegistration | None:
        with self._lock:
            return self._entries.get(service)

    def has(self, service: str | type) -> bool:
        with self._lock:
            return service in self._entries

    def remove(self, service: str | type) -> bool:
        with self._lock:
            if service in self._entries:
                del self._entries[service]
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def all(self) -> list[ServiceRegistration]:
        with self._lock:
            return list(self._entries.values())

    def keys(self) -> list[str | type]:
        with self._lock:
            return list(self._entries.keys())

    def count(self) -> int:
        with self._lock:
            return len(self._entries)

    def find_by_tag(self, tag: str) -> list[ServiceRegistration]:
        with self._lock:
            return [e for e in self._entries.values() if tag in e.tags]

    def find_by_lifetime(
        self,
        lifetime: Lifetime,
    ) -> list[ServiceRegistration]:
        with self._lock:
            return [e for e in self._entries.values() if e.lifetime == lifetime]
