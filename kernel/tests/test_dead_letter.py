import pytest

from kernel.events.dead_letter import DeadLetterEntry, DeadLetterQueue
from kernel.events.event import Event
from kernel.events.event_bus import EventBus
from kernel.events.retry import RetryPolicy
from kernel.events.subscription import Subscription


@pytest.fixture
def fast_retry_bus():
    return EventBus(
        retry_policy=RetryPolicy(
            max_attempts=3,
            initial_delay=0.01,
            backoff_multiplier=2.0,
            max_delay=0.1,
        ),
    )


@pytest.mark.asyncio
async def test_dlq_standalone_add_and_count():
    dlq = DeadLetterQueue()
    assert dlq.count() == 0

    entry = DeadLetterEntry(
        event=Event(name="test"),
        attempts=3,
        exception="timeout",
        subscriber="handler",
    )
    dlq.add(entry)
    assert dlq.count() == 1


@pytest.mark.asyncio
async def test_dlq_latest_returns_most_recent():
    dlq = DeadLetterQueue()
    for i in range(5):
        dlq.add(
            DeadLetterEntry(
                event=Event(name=f"e{i}"),
                attempts=1,
                exception="err",
                subscriber="h",
            ),
        )
    latest = dlq.latest(limit=2)
    assert len(latest) == 2
    assert latest[0].event.name == "e3"
    assert latest[1].event.name == "e4"


@pytest.mark.asyncio
async def test_dlq_clear():
    dlq = DeadLetterQueue()
    dlq.add(
        DeadLetterEntry(
            event=Event(name="t"), attempts=1, exception="x", subscriber="h",
        ),
    )
    dlq.clear()
    assert dlq.count() == 0


@pytest.mark.asyncio
async def test_dlq_all():
    dlq = DeadLetterQueue()
    dlq.add(
        DeadLetterEntry(
            event=Event(name="a"), attempts=1, exception="x", subscriber="h",
        ),
    )
    dlq.add(
        DeadLetterEntry(
            event=Event(name="b"), attempts=1, exception="x", subscriber="h",
        ),
    )
    all_entries = dlq.all()
    assert len(all_entries) == 2
    assert all_entries[0].event.name == "a"
    assert all_entries[1].event.name == "b"


@pytest.mark.asyncio
async def test_dlq_max_capacity():
    dlq = DeadLetterQueue(max_entries=3)
    for i in range(5):
        dlq.add(
            DeadLetterEntry(
                event=Event(name=f"e{i}"),
                attempts=1,
                exception="x",
                subscriber="h",
            ),
        )
    assert dlq.count() == 3
    names = [e.event.name for e in dlq.all()]
    assert names == ["e2", "e3", "e4"]


@pytest.mark.asyncio
async def test_failed_event_added_to_dlq_after_retry_exhaustion(fast_retry_bus):
    bus = fast_retry_bus
    bus.start()

    async def handler(event: Event):
        raise ValueError("always fails")

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()
    await bus.shutdown()

    assert bus.dead_letter_count() == 1
    entry = bus.dead_letters()[0]
    assert entry.event.name == "t"
    assert entry.attempts == 3
    assert entry.exception == "always fails"
    assert entry.subscriber == "handler"


@pytest.mark.asyncio
async def test_successful_event_not_in_dlq(fast_retry_bus):
    bus = fast_retry_bus
    bus.start()

    async def handler(event: Event):
        pass

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()
    await bus.shutdown()

    assert bus.dead_letter_count() == 0


@pytest.mark.asyncio
async def test_transient_failure_not_in_dlq(fast_retry_bus):
    bus = fast_retry_bus
    bus.start()
    call_count = 0

    async def handler(event: Event):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("transient")

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()
    await bus.shutdown()

    assert bus.dead_letter_count() == 0
    assert call_count == 3


@pytest.mark.asyncio
async def test_dlq_entry_metadata():
    bus = EventBus(
        retry_policy=RetryPolicy(
            max_attempts=2,
            initial_delay=0.01,
            backoff_multiplier=1.0,
            max_delay=0.1,
        ),
    )
    bus.start()

    async def handler(event: Event):
        raise TimeoutError("db timeout")

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()
    await bus.shutdown()

    entry = bus.dead_letters()[0]
    assert entry.exception_type == "TimeoutError"
    assert entry.exception == "db timeout"
    assert entry.attempts == 2
    assert entry.subscriber == "handler"
    assert entry.event.name == "t"
    assert entry.failed_at is not None
    assert entry.id is not None


@pytest.mark.asyncio
async def test_replay_dead_letters_republishes(fast_retry_bus):
    bus = fast_retry_bus
    bus.start()
    received = []

    async def failing_handler(event: Event):
        raise ValueError("fail")

    async def recording_handler(event: Event):
        received.append(event.name)

    await bus.register(Subscription(topic="t", handler=failing_handler))
    await bus.publish(Event(name="t"))
    await bus.join()

    assert bus.dead_letter_count() == 1

    # Restart dispatch (crashed after retry exhaustion) and replace handler
    bus.start()
    await bus.unregister("t", failing_handler)
    await bus.register(Subscription(topic="t", handler=recording_handler))
    await bus.replay_dead_letters()
    await bus.join()

    assert bus.dead_letter_count() == 0
    assert received == ["t"]


@pytest.mark.asyncio
async def test_replay_dead_letters_goes_through_publish_pipeline(
    fast_retry_bus,
):
    bus = fast_retry_bus
    bus.start()
    pipeline = []

    class PipelineMiddleware:
        async def before_publish(self, event: Event) -> Event:
            pipeline.append("before_publish")
            return event

        async def after_publish(self, event: Event) -> None:
            pipeline.append("after_publish")

    bus.add_middleware(PipelineMiddleware())

    async def failing_handler(event: Event):
        raise ValueError("fail")

    await bus.register(Subscription(topic="t", handler=failing_handler))
    await bus.publish(Event(name="t"))
    await bus.join()

    pipeline.clear()
    bus.start()
    await bus.unregister("t", failing_handler)

    async def recording_handler(event: Event):
        pass

    await bus.register(Subscription(topic="t", handler=recording_handler))
    await bus.replay_dead_letters()
    await bus.join()

    assert "before_publish" in pipeline
    assert "after_publish" in pipeline


@pytest.mark.asyncio
async def test_multiple_failed_events_in_dlq(fast_retry_bus):
    bus = fast_retry_bus
    bus.start()

    async def handler(event: Event):
        raise ValueError("fail")

    await bus.register(Subscription(topic="*", handler=handler))
    await bus.publish(Event(name="a"))
    await bus.publish(Event(name="b"))
    await bus.publish(Event(name="c"))
    await bus.join()
    await bus.shutdown()

    assert bus.dead_letter_count() == 3
    names = [e.event.name for e in bus.dead_letters()]
    assert names == ["a", "b", "c"]


@pytest.mark.asyncio
async def test_clear_dead_letters(fast_retry_bus):
    bus = fast_retry_bus
    bus.start()

    async def handler(event: Event):
        raise ValueError("fail")

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()

    assert bus.dead_letter_count() == 1
    bus.clear_dead_letters()
    assert bus.dead_letter_count() == 0


@pytest.mark.asyncio
async def test_dlq_does_not_affect_other_subscribers(fast_retry_bus):
    bus = fast_retry_bus
    bus.start()
    good_received = []

    async def bad_handler(event: Event):
        raise ValueError("fail")

    async def good_handler(event: Event):
        good_received.append(event.name)

    await bus.register(Subscription(topic="t", handler=bad_handler))
    await bus.register(Subscription(topic="t", handler=good_handler))
    await bus.publish(Event(name="t"))
    await bus.join()
    await bus.shutdown()

    assert bus.dead_letter_count() == 1
    assert good_received == ["t"]
