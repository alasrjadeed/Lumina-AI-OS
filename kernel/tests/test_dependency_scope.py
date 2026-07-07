from kernel.dependency.container import DIContainer
from kernel.dependency.lifetime import Lifetime
from kernel.dependency.scope import Scope


class _ScopedService:
    def __init__(self) -> None:
        self.id = id(self)


class _Repo:
    def __init__(self) -> None:
        self.id = id(self)


class _Outer:
    def __init__(self, inner: _ScopedService) -> None:
        self.inner = inner


def test_create_scope():
    container = DIContainer()
    scope = container.create_scope()
    assert scope is not container
    assert scope._parent is container


def test_scoped_isolation_between_scopes():
    container = DIContainer()
    container.register_type(_ScopedService, lifetime=Lifetime.SCOPED)

    scope1 = container.create_scope()
    scope2 = container.create_scope()

    a = scope1.resolve(_ScopedService)
    b = scope2.resolve(_ScopedService)
    assert a is not b


def test_scoped_same_within_scope():
    container = DIContainer()
    container.register_type(_ScopedService, lifetime=Lifetime.SCOPED)

    a = container.resolve(_ScopedService)
    b = container.resolve(_ScopedService)
    assert a is b


def test_singleton_shared_across_scopes():
    container = DIContainer()
    container.register_type(_Repo, lifetime=Lifetime.SINGLETON)

    scope1 = container.create_scope()
    scope2 = container.create_scope()

    a = container.resolve(_Repo)
    b = scope1.resolve(_Repo)
    c = scope2.resolve(_Repo)
    assert a is b
    assert b is c


def test_transient_always_new_in_scope():
    container = DIContainer()
    container.register_type(_ScopedService, lifetime=Lifetime.TRANSIENT)

    scope = container.create_scope()
    a = scope.resolve(_ScopedService)
    b = scope.resolve(_ScopedService)
    assert a is not b


def test_scoped_with_dependencies():
    container = DIContainer()
    container.register_type(_ScopedService, lifetime=Lifetime.SCOPED)
    container.register_type(_Outer, lifetime=Lifetime.SCOPED)

    outer = container.resolve(_Outer)
    assert isinstance(outer, _Outer)
    assert isinstance(outer.inner, _ScopedService)


def test_dispose_scope():
    container = DIContainer()
    container.register_type(_ScopedService, lifetime=Lifetime.SCOPED)

    a = container.resolve(_ScopedService)
    container.dispose_scope()

    b = container.resolve(_ScopedService)
    assert a is not b


def test_scope_class_wraps_container():
    container = DIContainer()
    container.register_type(_ScopedService, lifetime=Lifetime.SCOPED)
    scope = Scope(container)
    assert scope._parent is container


def test_scope_class_resolve():
    container = DIContainer()
    container.register_instance("key", "value")
    scope = Scope(container)
    assert scope.resolve("key") == "value"


def test_scope_class_try_resolve():
    container = DIContainer()
    scope = Scope(container)
    assert scope.try_resolve("missing") is None


def test_scope_class_dispose():
    container = DIContainer()
    container.register_type(_ScopedService, lifetime=Lifetime.SCOPED)
    scope = Scope(container)
    a = scope.resolve(_ScopedService)
    b = scope.resolve(_ScopedService)
    assert a is b
    scope.dispose()
    c = scope.resolve(_ScopedService)
    assert a is not c
