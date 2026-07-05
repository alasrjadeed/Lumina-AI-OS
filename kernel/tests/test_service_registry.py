import pytest
from kernel.services.service_registry import ServiceRegistry, ServiceStatus


class MockLogger:
    pass


class MockDatabase:
    pass


@pytest.fixture
def registry():
    return ServiceRegistry()


def test_register_service(registry):
    registry.register("logger", MockLogger)
    svc = registry.get("logger")
    assert svc is not None
    assert svc.name == "logger"
    assert svc.status == ServiceStatus.REGISTERED


def test_register_duplicate_fails(registry):
    registry.register("logger", MockLogger)
    with pytest.raises(ValueError):
        registry.register("logger", MockLogger)


def test_set_and_get_status(registry):
    registry.register("db", MockDatabase)
    registry.set_status("db", ServiceStatus.RUNNING)
    assert registry.get_status("db") == ServiceStatus.RUNNING


def test_dependency_order(registry):
    registry.register("db", MockDatabase)
    registry.register(
        "service",
        MockLogger,
        dependencies={"db"},
    )
    order = registry.resolve_dependency_order()
    assert order.index("db") < order.index("service")


def test_circular_dependency(registry):
    registry.register("a", MockLogger, dependencies={"b"})
    registry.register("b", MockLogger, dependencies={"a"})
    with pytest.raises(ValueError, match="Circular dependency"):
        registry.resolve_dependency_order()


def test_unregister(registry):
    registry.register("logger", MockLogger)
    assert registry.unregister("logger") is True
    assert registry.get("logger") is None
    assert registry.unregister("nonexistent") is False
