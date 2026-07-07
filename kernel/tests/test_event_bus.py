import pytest

from kernel.events.event import Event
from kernel.events.exceptions import DuplicateSubscriberError
from kernel.events.subscription import Subscription

pytestmark = pytest.mark.asyncio


async def test_register_and_publish(started_bus):
    bus = started_bus
    received = []

    async def handler(event: Event):
        received.append((event.name, event.payload))

    await bus.register(
        Subscription(topic="test.event", handler=handler),
    )
    await bus.publish(Event(name="test.event", payload={"key": "value"}))
    await bus.join()

    assert len(received) == 1
    assert received[0] == ("test.event", {"key": "value"})


async def test_wildcard_subscriber(started_bus):
    bus = started_bus
    received = []

    async def handler(event: Event):
        received.append(event.name)

    await bus.register(Subscription(topic="*", handler=handler))
    await bus.publish(Event(name="any.event"))
    await bus.publish(Event(name="another.event"))
    await bus.join()

    assert len(received) == 2


async def test_unregister(started_bus):
    bus = started_bus
    received = []

    async def handler(event: Event):
        received.append(event.name)

    await bus.register(Subscription(topic="test", handler=handler))
    await bus.unregister("test", handler)
    await bus.publish(Event(name="test"))
    await bus.join()

    assert len(received) == 0


async def test_handler_error_does_not_break_bus(started_bus):
    bus = started_bus
    received = []

    async def bad_handler(event: Event):
        raise ValueError("boom")

    async def good_handler(event: Event):
        received.append("ok")

    await bus.register(Subscription(topic="test", handler=bad_handler))
    await bus.register(Subscription(topic="test", handler=good_handler))
    await bus.publish(Event(name="test"))
    await bus.join()

    assert received == ["ok"]


async def test_duplicate_registration_raises(bus):
    async def handler(event: Event):
        pass

    await bus.register(Subscription(topic="test", handler=handler))

    with pytest.raises(DuplicateSubscriberError):
        await bus.register(Subscription(topic="test", handler=handler))


async def test_unregister_unknown_returns_false(bus):
    async def handler(event: Event):
        pass

    result = await bus.unregister("nonexistent", handler)
    assert result is False


async def test_subscriber_count(bus):
    async def handler(event: Event):
        pass

    assert bus.subscriber_count("test") == 0

    await bus.register(Subscription(topic="test", handler=handler))
    assert bus.subscriber_count("test") == 1


async def test_topics(bus):
    async def handler(event: Event):
        pass

    assert bus.topics() == []

    await bus.register(Subscription(topic="alpha", handler=handler))
    await bus.register(Subscription(topic="beta", handler=handler))
    assert bus.topics() == ["alpha", "beta"]


async def test_priority_order(started_bus):
    bus = started_bus
    order = []

    async def first(event: Event):
        order.append("first")

    async def second(event: Event):
        order.append("second")

    async def third(event: Event):
        order.append("third")

    await bus.register(Subscription(topic="test", handler=third, priority=300))
    await bus.register(Subscription(topic="test", handler=first, priority=100))
    await bus.register(Subscription(topic="test", handler=second, priority=200))
    await bus.publish(Event(name="test"))
    await bus.join()

    assert order == ["first", "second", "third"]


async def test_disabled_subscription_does_not_run(started_bus):
    bus = started_bus
    received = []

    async def handler(event: Event):
        received.append("ran")

    await bus.register(
        Subscription(topic="test", handler=handler, enabled=False),
    )
    await bus.publish(Event(name="test"))
    await bus.join()

    assert len(received) == 0


async def test_has_subscribers(bus):
    async def handler(event: Event):
        pass

    assert bus.has_subscribers("test") is False

    await bus.register(Subscription(topic="test", handler=handler))
    assert bus.has_subscribers("test") is True


async def test_clear(bus):
    async def handler(event: Event):
        pass

    await bus.register(Subscription(topic="a", handler=handler))
    await bus.register(Subscription(topic="b", handler=handler))
    assert bus.topics() == ["a", "b"]

    bus.clear()
    assert bus.topics() == []


async def test_queue_size(started_bus):
    bus = started_bus

    async def handler(event: Event):
        pass

    await bus.register(Subscription(topic="t", handler=handler))
    assert bus.queue_size() == 0

    await bus.publish(Event(name="t"))
    await bus.join()

    assert bus.queue_size() == 0


async def test_publish_empty_event_name_raises(bus):
    """Event validates name at construction time — publish never sees it."""
    with pytest.raises(ValueError, match="non-empty string"):
        Event(name="")


async def test_wildcard_prefix_match(started_bus):
    bus = started_bus
    received = []

    async def handler(event: Event):
        received.append(event.name)

    await bus.register(Subscription(topic="browser.**", handler=handler))
    await bus.publish(Event(name="browser.started"))
    await bus.publish(Event(name="browser.tab.created"))
    await bus.publish(Event(name="browser.closed"))
    await bus.join()

    assert received == ["browser.started", "browser.tab.created", "browser.closed"]


async def test_wildcard_prefix_does_not_match_other(started_bus):
    bus = started_bus
    received = []

    async def handler(event: Event):
        received.append(event.name)

    await bus.register(Subscription(topic="seo.*", handler=handler))
    await bus.publish(Event(name="browser.started"))
    await bus.publish(Event(name="crm.lead.created"))
    await bus.join()

    assert len(received) == 0


async def test_nested_wildcard_matches_exact_topic(started_bus):
    bus = started_bus
    received = []

    async def handler(event: Event):
        received.append(event.name)

    await bus.register(Subscription(topic="kernel.*", handler=handler))
    await bus.publish(Event(name="kernel"))
    await bus.join()

    assert received == ["kernel"]


async def test_multiple_events_in_order(started_bus):
    bus = started_bus
    order = []

    async def handler(event: Event):
        order.append(event.payload)

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t", payload="a"))
    await bus.publish(Event(name="t", payload="b"))
    await bus.publish(Event(name="t", payload="c"))
    await bus.join()

    assert order == ["a", "b", "c"]


async def test_equal_priority_preserves_registration_order(started_bus):
    bus = started_bus
    order = []

    async def first(event: Event):
        order.append("first")

    async def second(event: Event):
        order.append("second")

    async def third(event: Event):
        order.append("third")

    await bus.register(Subscription(topic="test", handler=first, priority=100))
    await bus.register(Subscription(topic="test", handler=second, priority=100))
    await bus.register(Subscription(topic="test", handler=third, priority=100))
    await bus.publish(Event(name="test"))
    await bus.join()

    assert order == ["first", "second", "third"]


async def test_wildcard_respects_priority(started_bus):
    bus = started_bus
    order = []

    async def high(event: Event):
        order.append("high")

    async def low(event: Event):
        order.append("low")

    await bus.register(Subscription(topic="*", handler=low, priority=200))
    await bus.register(Subscription(topic="*", handler=high, priority=100))
    await bus.publish(Event(name="any.event"))
    await bus.join()

    assert order == ["high", "low"]


async def test_priority_with_disabled_mixed(started_bus):
    bus = started_bus
    order = []

    async def first(event: Event):
        order.append("first")

    async def second(event: Event):
        order.append("second")

    async def third(event: Event):
        order.append("third")

    await bus.register(Subscription(topic="test", handler=first, priority=100))
    await bus.register(
        Subscription(topic="test", handler=second, priority=200, enabled=False),
    )
    await bus.register(Subscription(topic="test", handler=third, priority=300))
    await bus.publish(Event(name="test"))
    await bus.join()

    assert order == ["first", "third"]
