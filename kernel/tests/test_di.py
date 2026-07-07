
from kernel.dependency import DIContainer
from kernel.dependency.lifetime import Lifetime


def test_bind_and_resolve():
    container = DIContainer()
    container.register_instance("logger", {"level": "INFO"})

    instance = container.resolve("logger")
    assert instance == {"level": "INFO"}


def test_singleton_returns_same_instance():
    container = DIContainer()
    container.register_instance("cache", {})

    a = container.resolve("cache")
    b = container.resolve("cache")
    assert a is b


def test_transient_returns_new_instance():
    container = DIContainer()

    class _Obj:
        pass

    container.register_type(_Obj, lifetime=Lifetime.TRANSIENT)

    a = container.resolve(_Obj)
    b = container.resolve(_Obj)
    assert a is not b
