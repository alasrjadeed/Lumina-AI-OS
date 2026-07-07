import pytest

from kernel.events import Event
from kernel.events.subscriber import Subscriber


@pytest.mark.asyncio
async def test_subscriber_calls_handler():
    results = []

    async def handler(event: Event):
        results.append(event.name)

    sub = Subscriber(handler)
    await sub.handle(Event(name="test"))
    assert results == ["test"]


@pytest.mark.asyncio
async def test_subscriber_handler_id_default():
    async def handler(event: Event):
        pass

    sub = Subscriber(handler)
    assert sub.handler_id == "handler"


@pytest.mark.asyncio
async def test_subscriber_handler_id_custom():
    async def handler(event: Event):
        pass

    sub = Subscriber(handler, handler_id="my-id")
    assert sub.handler_id == "my-id"


@pytest.mark.asyncio
async def test_subscriber_handle():
    results = []

    async def handler(event: Event):
        results.append(event.name)

    sub = Subscriber(handler)
    await sub.handle(Event(name="alpha"))
    await sub.handle(Event(name="beta"))
    assert results == ["alpha", "beta"]
