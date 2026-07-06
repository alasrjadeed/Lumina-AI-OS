import pytest

from kernel.dependency.container import DIContainer
from kernel.dependency.exceptions import (
    CircularDependencyError,
    ServiceNotFoundError,
)
from kernel.dependency.lifetime import Lifetime


class _Repo:
    def __init__(self) -> None:
        self.id = id(self)


class _Service:
    def __init__(self, repo: _Repo) -> None:
        self.repo = repo


class _OptionalService:
    def __init__(self, repo: _Repo | None = None) -> None:
        self.repo = repo


class _CircularA:
    def __init__(self, b: "_CircularB") -> None:
        self.b = b


class _CircularB:
    def __init__(self, a: _CircularA) -> None:
        self.a = a


def test_register_type_and_resolve():
    container = DIContainer()
    container.register_type(_Repo)
    instance = container.resolve(_Repo)
    assert isinstance(instance, _Repo)


def test_resolve_not_found_raises():
    container = DIContainer()
    with pytest.raises(ServiceNotFoundError):
        container.resolve("nonexistent")


def test_register_instance():
    container = DIContainer()
    obj = {"key": "value"}
    container.register_instance("config", obj)
    assert container.resolve("config") is obj


def test_register_factory():
    container = DIContainer()
    container.register_factory(
        "counter",
        lambda c: {"count": 0},
    )
    instance = container.resolve("counter")
    assert instance == {"count": 0}


def test_singleton_returns_same_instance():
    container = DIContainer()
    container.register_type(_Repo, lifetime=Lifetime.SINGLETON)
    a = container.resolve(_Repo)
    b = container.resolve(_Repo)
    assert a is b


def test_transient_returns_new_instance():
    container = DIContainer()
    container.register_type(_Repo, lifetime=Lifetime.TRANSIENT)
    a = container.resolve(_Repo)
    b = container.resolve(_Repo)
    assert a is not b


def test_constructor_injection():
    container = DIContainer()
    container.register_type(_Repo, lifetime=Lifetime.SINGLETON)
    container.register_type(_Service)
    instance = container.resolve(_Service)
    assert isinstance(instance, _Service)
    assert isinstance(instance.repo, _Repo)


def test_optional_dependency():
    container = DIContainer()
    container.register_type(_OptionalService)
    instance = container.resolve(_OptionalService)
    assert isinstance(instance, _OptionalService)
    assert instance.repo is None


def test_circular_dependency_detected():
    container = DIContainer()
    container.register_type(_CircularA)
    container.register_type(_CircularB)
    with pytest.raises(CircularDependencyError):
        container.resolve(_CircularA)


def test_name_resolution():
    container = DIContainer()
    container.register_instance("db", "connected")
    assert container.resolve_name("db") == "connected"


def test_has():
    container = DIContainer()
    assert container.has("x") is False
    container.register_instance("x", 1)
    assert container.has("x") is True


def test_is_registered():
    container = DIContainer()
    assert container.is_registered("x") is False
    container.register_instance("x", 1)
    assert container.is_registered("x") is True


def test_registered_lists_services():
    container = DIContainer()
    container.register_instance("a", 1)
    container.register_instance("b", 2)
    services = container.registered()
    assert "a" in services
    assert "b" in services


def test_clear():
    container = DIContainer()
    container.register_instance("a", 1)
    assert container.has("a") is True
    container.clear()
    assert container.has("a") is False


def test_singleton_with_constructor_injection():
    container = DIContainer()
    container.register_type(_Repo, lifetime=Lifetime.SINGLETON)
    container.register_type(_Service, lifetime=Lifetime.SINGLETON)
    a = container.resolve(_Service)
    b = container.resolve(_Service)
    assert a is b
    assert a.repo is b.repo


def test_factory_provider_with_container():
    container = DIContainer()
    container.register_type(_Repo, lifetime=Lifetime.SINGLETON)

    def build_repo(c):
        return c.resolve(_Repo)

    container.register_factory("factory_repo", build_repo)
    instance = container.resolve("factory_repo")
    assert isinstance(instance, _Repo)


def test_scoped_lifetime():
    container = DIContainer()
    container.register_type(_Repo, lifetime=Lifetime.SCOPED)
    a = container.resolve(_Repo)
    b = container.resolve(_Repo)
    assert a is b


def test_named_register_type():
    container = DIContainer()
    container.register_type("repo_primary", _Repo, lifetime=Lifetime.SINGLETON)
    container.register_type("repo_secondary", _Repo, lifetime=Lifetime.TRANSIENT)
    primary = container.resolve("repo_primary")
    secondary = container.resolve("repo_secondary")
    assert isinstance(primary, _Repo)
    assert isinstance(secondary, _Repo)


def test_try_resolve_found():
    container = DIContainer()
    container.register_instance("x", 42)
    assert container.try_resolve("x") == 42


def test_try_resolve_not_found_returns_none():
    container = DIContainer()
    assert container.try_resolve("nonexistent") is None


def test_try_resolve_circular_returns_none():
    container = DIContainer()
    container.register_type(_CircularA)
    container.register_type(_CircularB)
    assert container.try_resolve(_CircularA) is None


def test_resolve_all():
    container = DIContainer()
    container.register_instance("a", 1)
    container.register_instance("b", 2)
    result = container.resolve_all()
    assert result == {"a": 1, "b": 2}


def test_register_delegate():
    container = DIContainer()
    container.register_type(_Repo, lifetime=Lifetime.SINGLETON)
    container.register_delegate(
        "repo_delegated",
        lambda c, r: c.resolve(_Repo),
    )
    instance = container.resolve("repo_delegated")
    assert isinstance(instance, _Repo)


def test_register_alias():
    container = DIContainer()
    obj = {"original": True}
    container.register_instance("original", obj)
    container.register_alias("alias", "original")
    assert container.resolve("alias") is obj
