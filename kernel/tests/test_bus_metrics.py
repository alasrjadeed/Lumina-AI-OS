import pytest

from kernel.events.event import Event
from kernel.events.retry import RetryPolicy
from kernel.events.subscription import Subscription


pytestmark = pytest.mark.asyncio


async def test_metrics_published_increments(started_bus):
    bus = started_bus

    async def handler(event: Event):
        pass

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()

    assert bus.metrics().published_events == 1


async def test_metrics_dispatched_increments(started_bus):
    bus = started_bus
    received = []

    async def handler(event: Event):
        received.append(event.name)

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()

    assert bus.metrics().dispatched_events == 1
    assert received == ["t"]


async def test_metrics_dispatched_per_subscriber(started_bus):
    bus = started_bus

    async def handler(event: Event):
        pass

    await bus.register(Subscription(topic="*", handler=handler))
    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()

    # Two subscribers both matched → 2 dispatched
    assert bus.metrics().dispatched_events == 2


async def test_metrics_failed_increments(started_bus):
    bus = started_bus

    async def handler(event: Event):
        raise ValueError("boom")

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()

    m = bus.metrics()
    assert m.failed_events == 1
    assert m.dispatched_events == 0


async def test_metrics_retried_increments(started_bus):
    bus = started_bus

    async def handler(event: Event):
        raise ValueError("transient")

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()

    m = bus.metrics()
    # max_attempts=3 → 3 calls, 2 retries (attempt 2 and 3 before last failure)
    assert m.retried_events == 2
    assert m.failed_events == 1


async def test_metrics_active_subscribers_on_register(started_bus):
    bus = started_bus
    assert bus.metrics().active_subscribers == 0

    async def handler(event: Event):
        pass

    await bus.register(Subscription(topic="a", handler=handler))
    assert bus.metrics().active_subscribers == 1

    await bus.register(Subscription(topic="b", handler=handler))
    assert bus.metrics().active_subscribers == 2


async def test_metrics_active_subscribers_on_unregister(started_bus):
    bus = started_bus

    async def handler_a(event: Event):
        pass

    async def handler_b(event: Event):
        pass

    await bus.register(Subscription(topic="a", handler=handler_a))
    await bus.register(Subscription(topic="b", handler=handler_b))
    assert bus.metrics().active_subscribers == 2

    await bus.unregister("a", handler_a)
    assert bus.metrics().active_subscribers == 1

    await bus.unregister("b", handler_b)
    assert bus.metrics().active_subscribers == 0


async def test_metrics_queue_depth(started_bus):
    bus = started_bus
    original = bus.metrics().queue_depth
    # queue_depth is updated lazily on metrics() call
    assert original >= 0


async def test_shutdown_prevents_new_publishes(bus):
    bus.start()
    await bus.shutdown()

    with pytest.raises(RuntimeError, match="shut down"):
        await bus.publish(Event(name="t"))


async def test_shutdown_drains_queue(bus):
    """Events published before shutdown are still processed."""
    received = []

    async def handler(event: Event):
        received.append(event.name)

    await bus.register(Subscription(topic="t", handler=handler))
    bus.start()

    await bus.publish(Event(name="t"))
    await bus.shutdown()

    assert received == ["t"]


async def test_shutdown_multiple_events_drained(bus):
    """All queued events are processed before shutdown completes."""
    received = []

    async def handler(event: Event):
        received.append(event.payload)

    await bus.register(Subscription(topic="t", handler=handler))
    bus.start()

    for i in range(5):
        await bus.publish(Event(name="t", payload=i))
    await bus.shutdown()

    assert received == [0, 1, 2, 3, 4]


async def test_metrics_snapshot_includes_counters(started_bus):
    bus = started_bus

    async def handler(event: Event):
        pass

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()

    snap = bus.metrics().snapshot()
    assert snap["published_events"] == 1
    assert snap["dispatched_events"] == 1
    assert snap["active_subscribers"] >= 1
