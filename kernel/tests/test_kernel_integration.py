from __future__ import annotations

import pytest

from kernel import Event, Kernel, di, event_bus, plugins, scheduler, services
from kernel.events.builtins.logging import LoggingMiddleware
from kernel.events.builtins.metrics import MetricsMiddleware
from kernel.events.builtins.tracing import TracingMiddleware
from kernel.events.builtins.validation import ValidationMiddleware
from kernel.events.subscription import Subscription


@pytest.fixture
def kernel():
    return Kernel(use_globals=False)


@pytest.fixture
def fresh_kernel():
    return Kernel(use_globals=False)


@pytest.mark.asyncio
async def test_init_publishes_initialized_event(kernel):
    received = []

    async def handler(event: Event):
        received.append(event.name)

    await kernel.event_bus.register(Subscription(topic="kernel.initialized", handler=handler))
    await kernel.init()
    await kernel.event_bus.join()
    await kernel.shutdown()

    assert "kernel.initialized" in received


@pytest.mark.asyncio
async def test_init_starts_event_bus(kernel):
    await kernel.init()

    assert kernel.event_bus._running
    assert kernel.event_bus._dispatch_task is not None

    await kernel.shutdown()


@pytest.mark.asyncio
async def test_init_is_idempotent(kernel):
    await kernel.init()
    await kernel.init()

    assert kernel._initialized

    await kernel.shutdown()


@pytest.mark.asyncio
async def test_shutdown_publishes_shutdown_event(kernel):
    received = []

    async def handler(event: Event):
        received.append(event.name)

    await kernel.event_bus.register(Subscription(topic="kernel.shutdown", handler=handler))
    await kernel.init()
    await kernel.shutdown()
    await kernel.event_bus.join()

    assert "kernel.shutdown" in received


@pytest.mark.asyncio
async def test_shutdown_stops_scheduler(kernel):
    await kernel.init()
    await kernel.shutdown()

    assert not kernel.scheduler._running
    assert kernel.scheduler._loop_task is None


@pytest.mark.asyncio
async def test_shutdown_stops_event_bus(kernel):
    await kernel.init()
    await kernel.shutdown()

    assert not kernel.event_bus._running


@pytest.mark.asyncio
async def test_double_shutdown_does_not_raise(kernel):
    await kernel.init()
    await kernel.shutdown()
    await kernel.shutdown()


@pytest.mark.asyncio
async def test_shutdown_without_init_does_not_raise(kernel):
    await kernel.shutdown()


@pytest.mark.asyncio
async def test_full_publish_consume_through_kernel(kernel):
    received = []

    async def handler(event: Event):
        received.append((event.name, event.payload))

    await kernel.event_bus.register(Subscription(topic="custom.event", handler=handler))
    await kernel.init()
    await kernel.event_bus.publish(Event(name="custom.event", payload=42))
    await kernel.event_bus.join()
    await kernel.shutdown()

    assert ("custom.event", 42) in received


@pytest.mark.asyncio
async def test_kernel_services_accessible(kernel):
    assert kernel.event_bus is not None
    assert kernel.services is not None
    assert kernel.plugins is not None
    assert kernel.scheduler is not None


@pytest.mark.asyncio
async def test_middleware_logging_works_in_kernel(kernel):
    mw = LoggingMiddleware(level="debug")
    kernel.event_bus.add_middleware(mw)
    await kernel.init()
    await kernel.event_bus.publish(Event(name="test.logging"))
    await kernel.event_bus.join()
    await kernel.shutdown()


@pytest.mark.asyncio
async def test_middleware_tracing_in_kernel(kernel):
    mw = TracingMiddleware()
    kernel.event_bus.add_middleware(mw)

    received = []

    async def handler(event: Event):
        received.append(event.correlation_id)

    await kernel.event_bus.register(Subscription(topic="trace.test", handler=handler))
    await kernel.init()
    await kernel.event_bus.publish(Event(name="trace.test"))
    await kernel.event_bus.join()
    await kernel.shutdown()

    assert len(received) == 1
    assert received[0] != ""


@pytest.mark.asyncio
async def test_middleware_validation_rejects(kernel):
    mw = ValidationMiddleware()
    kernel.event_bus.add_middleware(mw)
    mw.add_validator("must.be.five", lambda ev: ev.payload == 5)

    await kernel.init()
    with pytest.raises(Exception, match="Validation failed"):
        await kernel.event_bus.publish(Event(name="must.be.five", payload=3))
    await kernel.shutdown()


@pytest.mark.asyncio
async def test_middleware_validation_allows(kernel):
    mw = ValidationMiddleware()
    kernel.event_bus.add_middleware(mw)
    mw.add_validator("must.be.five", lambda ev: ev.payload == 5)

    received = []

    async def handler(event: Event):
        received.append(event.payload)

    await kernel.event_bus.register(Subscription(topic="must.be.five", handler=handler))
    await kernel.init()
    await kernel.event_bus.publish(Event(name="must.be.five", payload=5))
    await kernel.event_bus.join()
    await kernel.shutdown()

    assert received == [5]


@pytest.mark.asyncio
async def test_middleware_metrics_in_kernel(kernel):
    mw = MetricsMiddleware()  # pyright: ignore[reportAbstractUsage]
    kernel.event_bus.add_middleware(mw)

    await kernel.init()
    await kernel.event_bus.publish(Event(name="metric.me"))
    await kernel.event_bus.join()
    await kernel.shutdown()

    assert mw._per_type["metric.me"].published == 1


@pytest.mark.asyncio
async def test_di_container_accessible(kernel):
    assert kernel.di.try_resolve("event_bus") is kernel.event_bus
    assert kernel.di.try_resolve("scheduler") is kernel.scheduler
    assert kernel.di.try_resolve("services") is kernel.services
    assert kernel.di.try_resolve("plugins") is kernel.plugins


@pytest.mark.asyncio
async def test_global_singletons_exist():
    assert di is not None
    assert event_bus is not None
    assert scheduler is not None
    assert services is not None
    assert plugins is not None


@pytest.mark.asyncio
async def test_scheduler_can_run_job_via_kernel(kernel):
    results = []

    def task():
        results.append("done")

    await kernel.init()
    await kernel.scheduler.add_job("test-job", task, delay=0)
    await kernel.event_bus.join()
    await kernel.shutdown()

    assert "done" in results
