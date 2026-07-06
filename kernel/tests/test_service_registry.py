import pytest


def test_register_and_resolve():
    from kernel.services.registry import ServiceRegistry

    registry = ServiceRegistry()
    registry.register("config", {"key": "value"})

    assert registry.resolve("config") == {"key": "value"}


def test_resolve_missing():
    from kernel.services.registry import ServiceRegistry
    from kernel.exceptions import ServiceNotFoundError

    registry = ServiceRegistry()

    with pytest.raises(ServiceNotFoundError):
        registry.resolve("nonexistent")


def test_register_factory():
    from kernel.services.registry import ServiceRegistry

    registry = ServiceRegistry()
    registry.register_factory("counter", lambda: {"count": 0})

    result = registry.resolve("counter")
    assert result == {"count": 0}


def test_has_and_list():
    from kernel.services.registry import ServiceRegistry

    registry = ServiceRegistry()
    registry.register("a", 1)

    assert registry.has("a") is True
    assert registry.has("b") is False
    assert "a" in registry.list()
