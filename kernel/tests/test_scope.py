import pytest

from kernel.dependency import DIContainer, Lifetime, Scope
from kernel.dependency.exceptions import ServiceNotFoundError


def test_scope_creates_child():
    parent = DIContainer()
    scope = Scope(parent)
    assert scope.resolve is not None


def test_scope_resolves_from_parent():
    parent = DIContainer()
    parent.register_instance("db", {"host": "localhost"})
    scope = Scope(parent)
    assert scope.resolve("db") == {"host": "localhost"}


def test_scope_isolates_scoped_instances():
    parent = DIContainer()

    class Dep:
        def __init__(self):
            self.n = 0

    parent.register_type("dep", Dep, lifetime=Lifetime.SCOPED)
    scope1 = Scope(parent)
    scope2 = Scope(parent)

    d1 = scope1.resolve("dep")
    d2 = scope2.resolve("dep")
    assert d1 is not d2

    d_parent = parent.resolve("dep")
    assert d_parent is not d1
    assert d_parent is not d2


def test_scope_shares_singletons():
    parent = DIContainer()

    class Dep:
        pass

    parent.register_type("dep", Dep, lifetime=Lifetime.SINGLETON)
    scope1 = Scope(parent)
    scope2 = Scope(parent)

    assert scope1.resolve("dep") is scope2.resolve("dep")
    assert parent.resolve("dep") is scope1.resolve("dep")


def test_scope_resolve_nonexistent_raises():
    parent = DIContainer()
    scope = Scope(parent)
    with pytest.raises(ServiceNotFoundError):
        scope.resolve("missing")


def test_scope_try_resolve():
    parent = DIContainer()
    parent.register_instance("a", 1)
    scope = Scope(parent)
    assert scope.try_resolve("a") == 1
    assert scope.try_resolve("missing") is None


def test_scope_dispose_clears_scoped():
    parent = DIContainer()

    class Dep:
        pass

    parent.register_type("dep", Dep, lifetime=Lifetime.SCOPED)
    scope = Scope(parent)
    d1 = scope.resolve("dep")
    scope.dispose()
    d2 = scope.resolve("dep")
    assert d1 is not d2
