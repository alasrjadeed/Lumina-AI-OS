import pytest

from kernel.events.event import Event
from kernel.events.subscription import Subscription


pytestmark = pytest.mark.asyncio


async def test_publish_stores_event(started_bus):
    bus = started_bus

    async def handler(event: Event):
        pass

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()

    assert bus.history_count() == 1
    assert bus.history()[0].name == "t"


async def test_multiple_publishes_all_stored(started_bus):
    bus = started_bus

    async def handler(event: Event):
        pass

    await bus.register(Subscription(topic="t", handler=handler))
    for i in range(5):
        await bus.publish(Event(name="t", payload=i))
    await bus.join()

    assert bus.history_count() == 5


async def test_history_clear(started_bus):
    bus = started_bus

    async def handler(event: Event):
        pass

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()
    assert bus.history_count() == 1

    bus.clear_history()
    assert bus.history_count() == 0


async def test_rejected_by_middleware_not_stored(started_bus):
    """If before_publish rejects, the event is NOT stored."""
    bus = started_bus

    class Rejector:
        async def before_publish(self, event: Event) -> Event:
            msg = "rejected"
            raise ValueError(msg)

        async def after_publish(self, event: Event) -> None:
            pass

    bus.add_middleware(Rejector())

    async def handler(event: Event):
        pass

    await bus.register(Subscription(topic="t", handler=handler))

    with pytest.raises(ValueError, match="rejected"):
        await bus.publish(Event(name="t"))

    assert bus.history_count() == 0


async def test_middleware_modifies_before_store(started_bus):
    """Modifications from before_publish are reflected in stored event."""
    bus = started_bus

    class Modifier:
        async def before_publish(self, event: Event) -> Event:
            return Event(
                name=event.name,
                payload={**(event.payload or {}), "middleware": True},
            )

        async def after_publish(self, event: Event) -> None:
            pass

    bus.add_middleware(Modifier())

    async def handler(event: Event):
        pass

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t", payload={"original": True}))
    await bus.join()

    stored = bus.history()[0]
    assert stored.payload == {"original": True, "middleware": True}


async def test_history_independent_of_subscribers(started_bus):
    """History records events even when no subscribers match."""
    bus = started_bus
    await bus.publish(Event(name="orphan"))
    await bus.join()

    assert bus.history_count() == 1
    assert bus.history()[0].name == "orphan"


async def test_replay_via_bus(started_bus):
    bus = started_bus
    received = []

    async def handler(event: Event):
        received.append((event.name, event.payload))

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t", payload=1))
    await bus.publish(Event(name="t", payload=2))
    await bus.join()

    # Replay through the same pipeline
    await bus.replay()
    await bus.join()

    # Original events + replayed events
    assert received == [(("t", 1)), (("t", 2)), (("t", 1)), (("t", 2))]


async def test_replayed_events_not_stored_again(started_bus):
    bus = started_bus

    async def handler(event: Event):
        pass

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t", payload=1))
    await bus.publish(Event(name="t", payload=2))
    await bus.join()

    assert bus.history_count() == 2

    await bus.replay()
    await bus.join()

    # Replayed events should NOT be stored again
    assert bus.history_count() == 2


async def test_replay_topic_via_bus(started_bus):
    bus = started_bus
    received = []

    async def handler(event: Event):
        received.append((event.name, event.payload))

    await bus.register(Subscription(topic="app.*", handler=handler))
    await bus.publish(Event(name="app.start", payload=1))
    await bus.publish(Event(name="other", payload=2))
    await bus.publish(Event(name="app.stop", payload=3))
    await bus.join()

    await bus.replay_topic("app.start")
    await bus.join()

    assert received == [("app.start", 1), ("app.stop", 3), ("app.start", 1)]


async def test_replay_source_via_bus(started_bus):
    bus = started_bus
    received = []

    async def handler(event: Event):
        received.append(event.name)

    await bus.register(Subscription(topic="*", handler=handler))
    await bus.publish(Event(name="a", source="plugin:seo"))
    await bus.publish(Event(name="b", source="kernel"))
    await bus.publish(Event(name="c", source="plugin:seo"))
    await bus.join()

    await bus.replay_source("plugin:seo")
    await bus.join()

    assert received == ["a", "b", "c", "a", "c"]


async def test_replay_plugins(started_bus):
    bus = started_bus
    received = []

    async def handler(event: Event):
        received.append(event.payload)

    await bus.register(Subscription(topic="plugin.loaded", handler=handler))
    await bus.publish(Event(name="plugin.loaded", payload="seo"))
    await bus.publish(Event(name="plugin.loaded", payload="crm"))
    await bus.publish(Event(name="other", payload="skip"))
    await bus.join()

    await bus.replay_plugins()
    await bus.join()

    assert received == ["seo", "crm", "seo", "crm"]


async def test_replay_where_via_bus(started_bus):
    bus = started_bus
    received = []

    async def handler(event: Event):
        received.append(event.payload)

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t", payload=1))
    await bus.publish(Event(name="t", payload=2))
    await bus.publish(Event(name="t", payload=3))
    await bus.join()

    await bus.replay_where(lambda e: e.payload and e.payload > 1)
    await bus.join()

    assert received == [1, 2, 3, 2, 3]


async def test_replay_passes_through_middleware(started_bus):
    bus = started_bus
    before_events = []

    class TrackingMiddleware:
        async def before_publish(self, event: Event) -> Event:
            before_events.append(event.name)
            return event

        async def after_publish(self, event: Event) -> None:
            pass

    bus.add_middleware(TrackingMiddleware())

    received = []

    async def handler(event: Event):
        received.append(event.name)

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()

    before_events.clear()
    received.clear()

    await bus.replay()
    await bus.join()

    assert before_events == ["t"]
    assert received == ["t"]


async def test_is_replay_flag_on_replayed_events(started_bus):
    bus = started_bus
    received = []

    async def handler(event: Event):
        received.append((event.name, event.is_replay))

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()

    received.clear()

    await bus.replay()
    await bus.join()

    # Replayed events should carry is_replay=True
    assert received == [("t", True)]


async def test_replay_empty_history_is_noop(started_bus):
    bus = started_bus

    async def handler(event: Event):
        pass

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.replay()
    await bus.join()

    assert bus.history_count() == 0
