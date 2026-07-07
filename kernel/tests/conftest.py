import pytest
import pytest_asyncio

from kernel.dependency import DIContainer
from kernel.events.event_bus import EventBus


@pytest.fixture
def bus():
    return EventBus()


@pytest.fixture
def container():
    return DIContainer()


@pytest.fixture
def container_bus(container):
    bus = EventBus(container=container)
    container.register_instance("event_bus", bus)
    return bus


@pytest_asyncio.fixture
async def started_bus(bus):
    bus.start()
    yield bus
    await bus.shutdown()


@pytest_asyncio.fixture
async def started_container_bus(container_bus):
    container_bus.start()
    yield container_bus
    await container_bus.shutdown()
