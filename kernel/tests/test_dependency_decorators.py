from kernel.dependency.container import DIContainer
from kernel.dependency.decorators import auto_register, inject, scoped, service, singleton
from kernel.dependency.lifetime import Lifetime
from kernel.tests import test_dependency_decorators as mod


@singleton()
class _DecoratedSingleton:
    def __init__(self) -> None:
        self.id = id(self)


@service()
class _DecoratedService:
    def __init__(self) -> None:
        self.id = id(self)


@scoped()
class _DecoratedScoped:
    def __init__(self) -> None:
        self.id = id(self)


class _WithInject:
    @inject()
    def method(self, x: int) -> int:
        return x * 2


def test_singleton_decorator_marks_class():
    assert _DecoratedSingleton.__di_registration__["lifetime"] == Lifetime.SINGLETON


def test_service_decorator_marks_class():
    assert _DecoratedService.__di_registration__["lifetime"] == Lifetime.TRANSIENT


def test_scoped_decorator_marks_class():
    assert _DecoratedScoped.__di_registration__["lifetime"] == Lifetime.SCOPED


def test_singleton_decorator_registers_in_container():
    container = DIContainer()

    class _X:
        pass

    singleton(container)(_X)
    a = container.resolve(_X)
    b = container.resolve(_X)
    assert a is b


def test_service_decorator_registers_in_container():
    container = DIContainer()

    class _Y:
        pass

    service(container)(_Y)
    a = container.resolve(_Y)
    b = container.resolve(_Y)
    assert a is not b


def test_inject_decorator_marks_function():
    obj = _WithInject()
    assert obj.method(5) == 10
    assert hasattr(obj.method, "__di_inject__")


def test_inject_with_container_resolves_dep():
    container = DIContainer()

    class MyDep:
        def __init__(self):
            self.value = 42

    container.register_type(MyDep, lifetime=Lifetime.SINGLETON)

    @inject(container=container)
    def needs_dep(dep: MyDep) -> int:
        return dep.value

    assert needs_dep() == 42


def test_inject_with_missing_type_uses_default():
    container = DIContainer()

    @inject(container=container)
    def with_default(x: int = 99) -> int:
        return x

    assert with_default() == 99


def test_inject_no_container_no_hints():
    @inject()
    def plain(x: int) -> int:
        return x

    assert plain(5) == 5


def test_auto_register_scans_modules():
    container = DIContainer()

    auto_register(container, mod)
    assert container.is_registered(_DecoratedSingleton)
    assert container.is_registered(_DecoratedService)
    assert container.is_registered(_DecoratedScoped)
    assert not container.is_registered(_WithInject)
