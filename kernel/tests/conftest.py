import pytest
import pytest_asyncio

from kernel.events.event_bus import EventBus


@pytest.fixture
def bus():
    return EventBus()


@pytest_asyncio.fixture
async def started_bus(bus):
    """Bus with dispatch loop running. Yields bus, shuts down on teardown."""
    bus.start()
    yield bus
    await bus.shutdown()
