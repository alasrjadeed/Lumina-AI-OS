import pytest

from kernel.dependency.container import DIContainer
from kernel.dependency.exceptions import DependencyError
from kernel.dependency.provider import (
    FactoryProvider,
    InstanceProvider,
    TypeProvider,
)


class _Repo:
    def __init__(self) -> None:
        self.id = id(self)


class _Service:
    def __init__(self, repo: _Repo) -> None:
        self.repo = repo


def test_type_provider():
    container = DIContainer()
    provider = TypeProvider(_Repo)
    instance = provider.create_instance(container, container._resolver)
    assert isinstance(instance, _Repo)


def test_type_provider_with_dependencies():
    container = DIContainer()
    container.register_type(_Repo)

    provider = TypeProvider(_Service)
    instance = provider.create_instance(container, container._resolver)
    assert isinstance(instance, _Service)
    assert isinstance(instance.repo, _Repo)


def test_instance_provider():
    provider = InstanceProvider(42)
    assert provider.create_instance(None, None) == 42


def test_instance_provider_returns_same():
    obj = {"key": "val"}
    provider = InstanceProvider(obj)
    assert provider.create_instance(None, None) is obj


def test_factory_provider():
    provider = FactoryProvider(lambda c: {"built": True})
    result = provider.create_instance(None, None)
    assert result == {"built": True}


def test_factory_provider_receives_container():
    container = DIContainer()
    container.register_instance("magic", 99)

    def factory(c):
        return {"magic": c.resolve("magic")}

    provider = FactoryProvider(factory)
    result = provider.create_instance(container, container._resolver)
    assert result == {"magic": 99}


def test_factory_provider_none_raises():
    provider = FactoryProvider(lambda c: None)
    with pytest.raises(DependencyError, match="returned None"):
        provider.create_instance(None, None)
