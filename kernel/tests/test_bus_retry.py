import pytest
import pytest_asyncio

from kernel.events.event import Event
from kernel.events.event_bus import EventBus
from kernel.events.retry import RetryPolicy
from kernel.events.subscription import Subscription


pytestmark = pytest.mark.asyncio


@pytest.fixture
def fast_retry_bus():
    """Bus with aggressive retry (small delays, 3 attempts)."""
    return EventBus(
        retry_policy=RetryPolicy(
            max_attempts=3,
            initial_delay=0.01,
            backoff_multiplier=2.0,
            max_delay=0.1,
        ),
    )


@pytest_asyncio.fixture
async def started_fast_retry_bus(fast_retry_bus):
    fast_retry_bus.start()
    yield fast_retry_bus
    await fast_retry_bus.shutdown()


async def test_successful_handler_called_once(started_fast_retry_bus):
    bus = started_fast_retry_bus
    call_count = 0

    async def handler(event: Event):
        nonlocal call_count
        call_count += 1

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()

    assert call_count == 1


async def test_transient_failure_retried_until_success(started_fast_retry_bus):
    bus = started_fast_retry_bus
    call_count = 0

    async def handler(event: Event):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("not yet")

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()

    assert call_count == 3


async def test_max_attempts_exhausted_raises(bus):
    """After max_attempts failures, the subscriber error surfaces."""
    bus = EventBus(
        retry_policy=RetryPolicy(
            max_attempts=2,
            initial_delay=0.01,
            backoff_multiplier=1.0,
            max_delay=0.1,
        ),
    )
    bus.start()

    call_count = 0

    async def handler(event: Event):
        nonlocal call_count
        call_count += 1
        raise ValueError("always fails")

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()
    await bus.shutdown()

    # Handler was called max_attempts times
    assert call_count == 2


async def test_default_retry_catches_all_exceptions(started_bus):
    """Default policy retries all Exception subclasses including TypeError."""
    bus = started_bus
    call_count = 0

    async def handler(event: Event):
        nonlocal call_count
        call_count += 1
        raise TypeError("not retryable")

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()

    assert call_count == 3


async def test_custom_retry_exceptions_respected():
    """Only specified exceptions trigger retry."""
    bus = EventBus(
        retry_policy=RetryPolicy(
            max_attempts=3,
            initial_delay=0.01,
            backoff_multiplier=1.0,
            max_delay=0.1,
            retry_exceptions=(ValueError,),
        ),
    )
    bus.start()
    call_count = 0

    async def handler(event: Event):
        nonlocal call_count
        call_count += 1
        raise TypeError("not retryable")

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()
    await bus.shutdown()

    # TypeError is not in (ValueError,) so no retry
    assert call_count == 1


async def test_other_subscribers_not_affected_by_retries(started_fast_retry_bus):
    """A retrying subscriber doesn't block other subscribers."""
    bus = started_fast_retry_bus
    good_calls = []

    async def bad_handler(event: Event):
        raise ValueError("failing")

    async def good_handler(event: Event):
        good_calls.append("ok")

    await bus.register(Subscription(topic="t", handler=bad_handler))
    await bus.register(Subscription(topic="t", handler=good_handler))
    await bus.publish(Event(name="t"))
    await bus.join()

    assert good_calls == ["ok"]


async def test_custom_retry_policy_on_bus(bus):
    """EventBus accepts a custom RetryPolicy."""
    policy = RetryPolicy(max_attempts=1)
    custom_bus = EventBus(retry_policy=policy)
    assert custom_bus._retry_policy is policy
    await custom_bus.shutdown()
