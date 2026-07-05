import pytest
from kernel.events.event_bus import EventBus
from kernel.events.event import Event, EventPriority


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.mark.asyncio
async def test_publish_and_subscribe(event_bus):
    received = []

    async def handler(event):
        received.append(event)

    event_bus.subscribe("test.event", handler)
    event = Event(name="test.event", data={"key": "value"})
    await event_bus.publish(event)

    assert len(received) == 1
    assert received[0].data["key"] == "value"


@pytest.mark.asyncio
async def test_unsubscribe(event_bus):
    received = []

    async def handler(event):
        received.append(event)

    sub = event_bus.subscribe("test.event", handler)
    await event_bus.publish(Event(name="test.event"))
    assert len(received) == 1

    event_bus.unsubscribe("test.event", sub)
    await event_bus.publish(Event(name="test.event"))
    assert len(received) == 1


@pytest.mark.asyncio
async def test_once_subscriber(event_bus):
    received = []

    async def handler(event):
        received.append(event)

    event_bus.subscribe("test.event", handler, once=True)
    await event_bus.publish(Event(name="test.event"))
    await event_bus.publish(Event(name="test.event"))

    assert len(received) == 1


@pytest.mark.asyncio
async def test_event_history(event_bus):
    for i in range(5):
        await event_bus.publish(Event(name=f"event.{i}"))

    history = event_bus.get_history()
    assert len(history) == 5


@pytest.mark.asyncio
async def test_filtered_subscriber(event_bus):
    received = []

    async def handler(event):
        received.append(event)

    event_bus.subscribe(
        "test.event",
        handler,
        filter_func=lambda e: e.data.get("important", False),
    )

    await event_bus.publish(Event(name="test.event", data={"important": False}))
    assert len(received) == 0

    await event_bus.publish(Event(name="test.event", data={"important": True}))
    assert len(received) == 1


@pytest.mark.asyncio
async def test_priority_order(event_bus):
    order = []

    async def handler_high(event):
        order.append("high")

    async def handler_low(event):
        order.append("low")

    event_bus.subscribe("test.event", handler_low, priority=0)
    event_bus.subscribe("test.event", handler_high, priority=100)

    await event_bus.publish(Event(name="test.event"))
    assert order == ["high", "low"]
