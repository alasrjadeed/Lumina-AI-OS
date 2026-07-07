import pytest

from kernel.events import Event, Publisher, Subscription


@pytest.mark.asyncio
async def test_publisher_publishes(started_bus):
    results = []

    async def handler(event: Event):
        results.append(event.payload)

    sub = Subscription("test.*", handler)
    await started_bus.register(sub)
    pub = Publisher(started_bus)
    await pub.publish(Event(name="test.hello", payload={"msg": "hi"}))

    await started_bus.join()
    assert results == [{"msg": "hi"}]


@pytest.mark.asyncio
async def test_publisher_restricted_api(started_bus):
    pub = Publisher(started_bus)
    assert not hasattr(pub, "register")
    assert not hasattr(pub, "unregister")
    assert not hasattr(pub, "dispatch")
    assert hasattr(pub, "publish")
