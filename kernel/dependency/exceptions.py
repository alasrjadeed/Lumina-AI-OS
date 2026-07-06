from __future__ import annotations


class DependencyError(Exception):
    """Base exception for all DI container errors."""


class ServiceNotFoundError(DependencyError):
    """Raised when a requested service is not registered."""

    def __init__(self, service: str) -> None:
        self.service = service
        super().__init__(f"Service not found: {service}")


class ServiceRegistrationError(DependencyError):
    """Raised when a service registration fails."""

    def __init__(self, service: str, message: str = "") -> None:
        self.service = service
        msg = f"Registration failed for '{service}'"
        if message:
            msg += f": {message}"
        super().__init__(msg)


class CircularDependencyError(DependencyError):
    """Raised when a circular dependency is detected."""

    def __init__(self, chain: list[str]) -> None:
        self.chain = chain
        path = " -> ".join(chain)
        super().__init__(f"Circular dependency detected: {path}")


class LifetimeError(DependencyError):
    """Raised when a lifetime operation is invalid."""
