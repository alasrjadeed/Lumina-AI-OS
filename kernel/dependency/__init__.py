from kernel.dependency.container import DIContainer
from kernel.dependency.decorators import auto_register, inject, scoped, service, singleton
from kernel.dependency.exceptions import (
    CircularDependencyError,
    DependencyError,
    LifetimeError,
    ServiceNotFoundError,
    ServiceRegistrationError,
)
from kernel.dependency.interfaces import IDisposable, IServiceProvider
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
from kernel.dependency.scope import Scope
from kernel.dependency.utils import ServiceKey, has_default, type_name

__all__ = [
    "DIContainer",
    "ServiceProvider",
    "TypeProvider",
    "InstanceProvider",
    "FactoryProvider",
    "DelegateProvider",
    "AliasProvider",
    "ServiceRegistration",
    "ServiceRegistry",
    "Resolver",
    "Scope",
    "Lifetime",
    "IServiceProvider",
    "IDisposable",
    "inject",
    "service",
    "singleton",
    "scoped",
    "auto_register",
    "DependencyError",
    "ServiceNotFoundError",
    "ServiceRegistrationError",
    "CircularDependencyError",
    "LifetimeError",
    "ServiceKey",
    "type_name",
    "has_default",
]
