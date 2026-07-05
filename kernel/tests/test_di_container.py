import pytest
from kernel.dependency.container import DIContainer, Lifetime


class Config:
    def __init__(self):
        self.value = 42


class Database:
    def __init__(self, config: Config = None):
        self.config = config


@pytest.fixture
def container():
    return DIContainer()


def test_singleton_lifetime(container):
    container.register("config", lambda: Config(), Lifetime.SINGLETON)
    a = container.resolve("config")
    b = container.resolve("config")
    assert a is b
    assert a.value == 42


def test_transient_lifetime(container):
    container.register("config", lambda: Config(), Lifetime.TRANSIENT)
    a = container.resolve("config")
    b = container.resolve("config")
    assert a is not b


def test_register_instance(container):
    cfg = Config()
    container.register_instance("config", cfg)
    assert container.resolve("config") is cfg


def test_scoped_lifetime(container):
    container.register("config", lambda: Config(), Lifetime.SCOPED)
    scope = container.create_scope()
    a = scope.resolve("config")
    b = scope.resolve("config")
    assert a is b
    scope.clear_scope()
    c = scope.resolve("config")
    assert a is not c


def test_has_and_remove(container):
    container.register("config", lambda: Config())
    assert container.has("config") is True
    container.remove("config")
    assert container.has("config") is False


def test_resolve_nonexistent(container):
    with pytest.raises(KeyError):
        container.resolve("nonexistent")
