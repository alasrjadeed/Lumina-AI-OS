import pytest

from kernel.dependency import (
    AliasProvider,
    DelegateProvider,
    DIContainer,
    Lifetime,
)
from kernel.dependency.exceptions import DependencyError, ServiceNotFoundError
from kernel.dependency.models import ServiceRegistration


def test_alias_provider_resolves_target():
    container = DIContainer()
    container.register_instance("real", {"key": 42})
    container._registry.register(ServiceRegistration("alias", AliasProvider("real")))
    assert container.resolve("alias") == {"key": 42}


def test_alias_provider_nonexistent_raises():
    container = DIContainer()
    container._registry.register(ServiceRegistration("bad", AliasProvider("missing")))
    with pytest.raises(ServiceNotFoundError):
        container.resolve("bad")


def test_delegate_provider_calls_func():
    container = DIContainer()
    resolver = container._resolver

    def maker(c, r):
        return {"from": "delegate"}

    provider = DelegateProvider(maker)
    result = provider.create_instance(container, resolver)
    assert result == {"from": "delegate"}


def test_delegate_provider_raises_on_none():
    container = DIContainer()
    resolver = container._resolver
    provider = DelegateProvider(lambda c, r: None)
    with pytest.raises(DependencyError):
        provider.create_instance(container, resolver)


def test_type_provider_resolves():
    container = DIContainer()

    class MyService:
        pass

    container.register_type("myservice", MyService, lifetime=Lifetime.SINGLETON)
    instance = container.resolve("myservice")
    assert isinstance(instance, MyService)


def test_factory_provider():
    container = DIContainer()

    def maker(c):
        return {"from": "factory"}

    container.register_factory("f", maker)
    assert container.resolve("f") == {"from": "factory"}


def test_instance_provider():
    container = DIContainer()
    obj = object()
    container.register_instance("obj", obj)
    assert container.resolve("obj") is obj
