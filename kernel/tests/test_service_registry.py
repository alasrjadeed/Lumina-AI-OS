from __future__ import annotations

import pytest

from kernel.dependency.lifetime import Lifetime
from kernel.exceptions import (
    CircularDependencyError,
    ServiceLifecycleError,
    ServiceNotFoundError,
)
from kernel.services.models import HealthStatus, ServiceStatus
from kernel.services.registry import ServiceRegistry

# ---------------------------------------------------------------------------
# Registration & resolution
# ---------------------------------------------------------------------------


def test_register_and_resolve():
    registry = ServiceRegistry()
    registry.register("config", {"key": "value"})
    assert registry.resolve("config") == {"key": "value"}


def test_resolve_missing():
    registry = ServiceRegistry()
    with pytest.raises(ServiceNotFoundError):
        registry.resolve("nonexistent")


def test_try_resolve():
    registry = ServiceRegistry()
    registry.register("a", 1)
    assert registry.try_resolve("a") == 1
    assert registry.try_resolve("missing") is None


def test_register_factory():
    registry = ServiceRegistry()
    registry.register_factory("counter", lambda c: {"count": 0})
    result = registry.resolve("counter")
    assert result == {"count": 0}


def test_register_type():
    class MyService:
        def __init__(self):
            self.value = 99

    registry = ServiceRegistry()
    registry.register_type("myservice", MyService, lifetime=Lifetime.SINGLETON)
    instance = registry.resolve("myservice")
    assert instance.value == 99
    assert registry.resolve("myservice") is instance


def test_register_many():
    registry = ServiceRegistry()
    registry.register_many({"a": 1, "b": 2})
    assert registry.resolve("a") == 1
    assert registry.resolve("b") == 2


def test_register_returns_record():
    registry = ServiceRegistry()
    record = registry.register("x", 42, tags={"t1"})
    assert record.name == "x"
    assert record.instance == 42
    assert "t1" in record.tags


# ---------------------------------------------------------------------------
# has / list / count / get
# ---------------------------------------------------------------------------


def test_has_and_list():
    registry = ServiceRegistry()
    registry.register("a", 1)
    assert registry.has("a") is True
    assert registry.has("b") is False
    assert "a" in registry.list()


def test_get():
    registry = ServiceRegistry()
    registry.register("a", 42)
    assert registry.get("a") == 42
    assert registry.get("missing") is None
    assert registry.get("missing", default="fallback") == "fallback"


def test_count():
    registry = ServiceRegistry()
    assert registry.count() == 0
    registry.register("a", 1)
    assert registry.count() == 1
    registry.register("b", 2)
    assert registry.count() == 2


# ---------------------------------------------------------------------------
# Removal
# ---------------------------------------------------------------------------


def test_remove():
    registry = ServiceRegistry()
    registry.register("a", 1)
    registry.remove("a")
    assert registry.has("a") is False


def test_remove_many():
    registry = ServiceRegistry()
    registry.register_many({"a": 1, "b": 2, "c": 3})
    registry.remove_many(["a", "c"])
    assert not registry.has("a")
    assert registry.has("b")
    assert not registry.has("c")


def test_remove_running_raises():
    registry = ServiceRegistry()
    registry.register("svc", "x")
    registry._records["svc"].status = ServiceStatus.RUNNING
    with pytest.raises(ServiceLifecycleError):
        registry.remove("svc")


def test_clear():
    registry = ServiceRegistry()
    registry.register_many({"a": 1, "b": 2})
    registry.clear()
    assert registry.count() == 0


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


def test_tag_and_find():
    registry = ServiceRegistry()
    registry.register("db", {"host": "localhost"}, tags={"database", "core"})
    registry.register("cache", {"ttl": 60}, tags={"cache"})
    registry.register("logger", {"level": "info"})
    assert registry.get_tags("db") == {"database", "core"}
    assert registry.get_tags("logger") == set()
    found = registry.find_by_tag("database")
    assert "db" in found
    assert "cache" not in found
    assert registry.find_by_tag("missing") == []


def test_tag_add_after_register():
    registry = ServiceRegistry()
    registry.register("x", 1)
    registry.tag("x", {"important"})
    assert "important" in registry.get_tags("x")


def test_untag():
    registry = ServiceRegistry()
    registry.register("x", 1, tags={"a", "b", "c"})
    registry.untag("x", {"b"})
    assert registry.get_tags("x") == {"a", "c"}


def test_tag_nonexistent_raises():
    registry = ServiceRegistry()
    with pytest.raises(ServiceNotFoundError):
        registry.tag("missing", {"x"})


def test_find_by_tag_ignores_removed():
    registry = ServiceRegistry()
    registry.register("x", 1, tags={"temp"})
    registry.register("y", 2, tags={"temp"})
    registry.remove("x")
    assert registry.find_by_tag("temp") == ["y"]


def test_list_by_tags():
    registry = ServiceRegistry()
    registry.register("db", {"a": 1}, tags={"database", "core"})
    registry.register("cache", {"b": 2}, tags={"cache", "core"})
    registry.register("queue", {"c": 3}, tags={"queue"})
    result = registry.list_by_tags({"core"})
    assert "db" in result
    assert "cache" in result
    assert "queue" not in result


def test_register_factory_with_tags():
    registry = ServiceRegistry()
    registry.register_factory("fn", lambda c: 42, tags={"magic"})
    assert registry.find_by_tag("magic") == ["fn"]
    assert registry.resolve("fn") == 42


def test_register_type_with_tags():
    class Foo:
        pass

    registry = ServiceRegistry()
    registry.register_type("foo", Foo, lifetime=Lifetime.SINGLETON, tags={"type"})
    assert registry.find_by_tag("type") == ["foo"]


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def test_find_by_status():
    registry = ServiceRegistry()
    registry.register("a", 1)
    registry.register("b", 2)
    registry._records["a"].status = ServiceStatus.RUNNING
    running = registry.find_by_status(ServiceStatus.RUNNING)
    assert "a" in running
    assert "b" not in running


def test_find_by_type():
    class Base:
        pass

    class Impl(Base):
        pass

    registry = ServiceRegistry()
    registry.register("impl", Impl())
    registry.register("other", "string")
    found = registry.find_by_type(Base)
    assert "impl" in found
    assert "other" not in found


def test_find_by_dependency():
    registry = ServiceRegistry()
    registry.register("db", 1, dependencies=["config"])
    registry.register("cache", 2, dependencies=["config"])
    registry.register("web", 3)
    found = registry.find_by_dependency("config")
    assert "db" in found
    assert "cache" in found
    assert "web" not in found


def test_get_record():
    registry = ServiceRegistry()
    registry.register("x", 99)
    record = registry.get_record("x")
    assert record is not None
    assert record.name == "x"
    assert registry.get_record("missing") is None


# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------


def test_health_no_checkers():
    registry = ServiceRegistry()
    registry.register("svc", "x")
    assert registry.health("svc") is None


def test_health_healthy():
    registry = ServiceRegistry()
    registry.register("svc", "x")
    registry.add_health_check("svc", lambda: HealthStatus.HEALTHY)
    assert registry.health("svc") is HealthStatus.HEALTHY


def test_health_unhealthy():
    registry = ServiceRegistry()
    registry.register("svc", "x")
    registry.add_health_check("svc", lambda: HealthStatus.UNHEALTHY)
    assert registry.health("svc") is HealthStatus.UNHEALTHY


def test_health_checker_exception():
    registry = ServiceRegistry()
    registry.register("svc", "x")

    def crash():
        raise RuntimeError("boom")

    registry.add_health_check("svc", crash)
    assert registry.health("svc") is HealthStatus.UNHEALTHY


def test_health_aggregates_worst():
    registry = ServiceRegistry()
    registry.register("svc", "x")
    registry.add_health_check("svc", lambda: HealthStatus.HEALTHY)
    registry.add_health_check("svc", lambda: HealthStatus.DEGRADED)
    assert registry.health("svc") is HealthStatus.DEGRADED
    registry.add_health_check("svc", lambda: HealthStatus.UNHEALTHY)
    assert registry.health("svc") is HealthStatus.UNHEALTHY


def test_remove_health_check():
    registry = ServiceRegistry()
    registry.register("svc", "x")

    def check():
        return HealthStatus.HEALTHY

    registry.add_health_check("svc", check)
    assert registry.remove_health_check("svc", check) is True
    assert registry.remove_health_check("svc", check) is False
    assert registry.health("svc") is None


def test_health_nonexistent_raises():
    registry = ServiceRegistry()
    with pytest.raises(ServiceNotFoundError):
        registry.health("missing")


def test_health_all():
    registry = ServiceRegistry()
    registry.register("a", 1)
    registry.register("b", 2)
    registry.add_health_check("a", lambda: HealthStatus.HEALTHY)
    results = registry.health_all()
    assert results["a"] is HealthStatus.HEALTHY
    assert results["b"] is None


# ---------------------------------------------------------------------------
# Lifecycle: start / stop
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_simple():
    registry = ServiceRegistry()
    registry.register("svc", 42)
    record = await _start(registry, "svc")
    assert record.status is ServiceStatus.RUNNING


@pytest.mark.asyncio
async def test_start_is_idempotent():
    registry = ServiceRegistry()
    registry.register("svc", 1)
    await registry.start("svc")
    await registry.start("svc")
    assert registry._records["svc"].status is ServiceStatus.RUNNING


@pytest.mark.asyncio
async def test_stop_simple():
    registry = ServiceRegistry()
    registry.register("svc", 1)
    await registry.start("svc")
    await registry.stop("svc")
    assert registry._records["svc"].status is ServiceStatus.STOPPED


@pytest.mark.asyncio
async def test_stop_is_idempotent():
    registry = ServiceRegistry()
    registry.register("svc", 1)
    await registry.start("svc")
    await registry.stop("svc")
    await registry.stop("svc")
    assert registry._records["svc"].status is ServiceStatus.STOPPED


@pytest.mark.asyncio
async def test_stop_before_start_raises():
    registry = ServiceRegistry()
    registry.register("svc", 1)
    with pytest.raises(ServiceLifecycleError):
        await registry.stop("svc")


@pytest.mark.asyncio
async def test_start_calls_initialize_on_iservice():
    calls = []

    class MyService:
        service_name = "test"

        async def initialize(self):
            calls.append("init")

        async def shutdown(self):
            calls.append("shutdown")

    registry = ServiceRegistry()
    registry.register("mysvc", MyService())
    await registry.start("mysvc")
    assert "init" in calls
    assert registry._records["mysvc"].status is ServiceStatus.RUNNING
    await registry.stop("mysvc")
    assert "shutdown" in calls
    assert registry._records["mysvc"].status is ServiceStatus.STOPPED


@pytest.mark.asyncio
async def test_start_failure_sets_failed():
    calls = []

    class BadService:
        service_name = "bad"

        async def initialize(self):
            calls.append("init")
            raise RuntimeError("init failed")

        async def shutdown(self):
            calls.append("shutdown")

    registry = ServiceRegistry()
    registry.register("bad", BadService())
    with pytest.raises(ServiceLifecycleError):
        await registry.start("bad")
    assert registry._records["bad"].status is ServiceStatus.FAILED
    assert "init" in calls


@pytest.mark.asyncio
async def test_shutdown_failure_sets_failed():
    calls = []

    class BadShutdown:
        service_name = "bad"

        async def initialize(self):
            calls.append("init")

        async def shutdown(self):
            calls.append("shutdown")
            raise RuntimeError("shutdown failed")

    registry = ServiceRegistry()
    registry.register("bad", BadShutdown())
    await registry.start("bad")
    with pytest.raises(ServiceLifecycleError):
        await registry.stop("bad")
    assert registry._records["bad"].status is ServiceStatus.FAILED
    assert "shutdown" in calls


# ---------------------------------------------------------------------------
# Lifecycle: start_all / stop_all
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_all_starts_created():
    registry = ServiceRegistry()
    registry.register("a", 1)
    registry.register("b", 2)
    await registry.start_all()
    assert registry._records["a"].status is ServiceStatus.RUNNING
    assert registry._records["b"].status is ServiceStatus.RUNNING


@pytest.mark.asyncio
async def test_stop_all_stops_running():
    registry = ServiceRegistry()
    registry.register("a", 1)
    registry.register("b", 2)
    await registry.start_all()
    await registry.stop_all()
    assert registry._records["a"].status is ServiceStatus.STOPPED
    assert registry._records["b"].status is ServiceStatus.STOPPED


@pytest.mark.asyncio
async def test_start_all_respects_dependencies():
    order: list[str] = []

    class OrderedService:
        def __init__(self, name):
            self.service_name = name

        async def initialize(self):
            order.append(self.service_name)

        async def shutdown(self):
            order.append(f"stop:{self.service_name}")

    registry = ServiceRegistry()
    registry.register("db", OrderedService("db"), dependencies=[])
    registry.register("cache", OrderedService("cache"), dependencies=["db"])
    registry.register("web", OrderedService("web"), dependencies=["cache"])
    await registry.start_all()
    db_idx = order.index("db")
    cache_idx = order.index("cache")
    web_idx = order.index("web")
    assert db_idx < cache_idx < web_idx


@pytest.mark.asyncio
async def test_stop_all_reverses_dependencies():
    order: list[str] = []

    class OrderedService:
        def __init__(self, name):
            self.service_name = name

        async def initialize(self):
            order.append(f"start:{self.service_name}")

        async def shutdown(self):
            order.append(f"stop:{self.service_name}")

    registry = ServiceRegistry()
    registry.register("db", OrderedService("db"), dependencies=[])
    registry.register("cache", OrderedService("cache"), dependencies=["db"])
    registry.register("web", OrderedService("web"), dependencies=["cache"])
    await registry.start_all()
    await registry.stop_all()
    start_db = order.index("start:db")
    start_cache = order.index("start:cache")
    start_web = order.index("start:web")
    stop_web = order.index("stop:web")
    stop_cache = order.index("stop:cache")
    stop_db = order.index("stop:db")
    assert start_db < start_cache < start_web
    assert stop_web < stop_cache < stop_db


# ---------------------------------------------------------------------------
# Dependency ordering / circular detection
# ---------------------------------------------------------------------------


def test_topological_sort():
    registry = ServiceRegistry()
    registry.register("leaf", 1, dependencies=[])
    registry.register("middle", 2, dependencies=["leaf"])
    registry.register("root", 3, dependencies=["middle"])
    order = registry._dependency_order()
    leaf_idx = order.index("leaf")
    middle_idx = order.index("middle")
    root_idx = order.index("root")
    assert leaf_idx < middle_idx < root_idx


def test_circular_dependency_detected():
    registry = ServiceRegistry()
    registry.register("a", 1, dependencies=["b"])
    registry.register("b", 2, dependencies=["a"])
    with pytest.raises(CircularDependencyError):
        registry._dependency_order()


def test_no_dependencies_order():
    registry = ServiceRegistry()
    registry.register("a", 1)
    registry.register("b", 2)
    order = registry._dependency_order()
    assert "a" in order
    assert "b" in order


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _start(registry, name):
    await registry.start(name)
    return registry._records[name]
