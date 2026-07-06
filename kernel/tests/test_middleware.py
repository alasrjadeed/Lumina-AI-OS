import pytest

from kernel.events.event import Event
from kernel.events.middleware import BaseMiddleware, EventMiddleware
from kernel.events.subscription import Subscription


class RecordingMiddleware(BaseMiddleware):
    """Simple middleware that records invocations."""

    def __init__(self) -> None:
        self.before_calls: list[Event] = []
        self.after_calls: list[Event] = []

    async def before_publish(self, event: Event) -> Event:
        self.before_calls.append(event)
        return event

    async def after_publish(self, event: Event) -> None:
        self.after_calls.append(event)


class ModifyingMiddleware(BaseMiddleware):
    """Middleware that adds a payload key."""

    async def before_publish(self, event: Event) -> Event:
        return Event(
            name=event.name,
            payload={**(event.payload or {}), "modified": True},
            timestamp=event.timestamp,
        )


class RejectingMiddleware(BaseMiddleware):
    """Middleware that rejects certain events."""

    def __init__(self, reject_name: str = "bad") -> None:
        self._reject_name = reject_name

    async def before_publish(self, event: Event) -> Event:
        if event.name == self._reject_name:
            msg = f"Event '{event.name}' is not allowed"
            raise ValueError(msg)
        return event


class FailingAfterMiddleware(BaseMiddleware):
    """Middleware that fails in after_publish but has no-op before."""

    async def after_publish(self, event: Event) -> None:
        msg = "after_publish failed"
        raise RuntimeError(msg)


class BrokenBeforeMiddleware(BaseMiddleware):
    """Middleware that fails in before_publish."""

    async def before_publish(self, event: Event) -> Event:
        msg = "before_publish failed"
        raise RuntimeError(msg)


pytestmark = pytest.mark.asyncio


async def test_middleware_execution_order(started_bus):
    """Middleware before_publish runs before enqueue, after_publish runs after."""
    bus = started_bus
    recorder = RecordingMiddleware()
    bus.add_middleware(recorder)

    received = []

    async def handler(event: Event):
        received.append(event.name)

    await bus.register(Subscription(topic="test", handler=handler))
    await bus.publish(Event(name="test"))
    await bus.join()

    assert len(recorder.before_calls) == 1
    assert len(recorder.after_calls) == 1
    assert recorder.before_calls[0].name == "test"
    assert recorder.after_calls[0].name == "test"
    assert len(received) == 1


async def test_middleware_can_modify_event(started_bus):
    """before_publish can transform the event."""
    bus = started_bus
    bus.add_middleware(ModifyingMiddleware())

    received = []

    async def handler(event: Event):
        received.append(event.payload)

    await bus.register(Subscription(topic="test", handler=handler))
    await bus.publish(Event(name="test", payload={"original": True}))
    await bus.join()

    assert len(received) == 1
    assert received[0] == {"original": True, "modified": True}


async def test_middleware_can_reject_event(started_bus):
    """before_publish that raises prevents enqueue."""
    bus = started_bus
    bus.add_middleware(RejectingMiddleware())

    received = []

    async def handler(event: Event):
        received.append(event.name)

    await bus.register(Subscription(topic="bad", handler=handler))

    with pytest.raises(ValueError, match="not allowed"):
        await bus.publish(Event(name="bad"))

    await bus.join()
    assert len(received) == 0


async def test_multiple_middleware_run_in_order(started_bus):
    """Middleware run in registration order."""
    bus = started_bus
    order = []

    class OrderedMiddleware:
        def __init__(self, label: str) -> None:
            self.label = label

        async def before_publish(self, event: Event) -> Event:
            order.append(f"before_{self.label}")
            return event

        async def after_publish(self, event: Event) -> None:
            order.append(f"after_{self.label}")

    bus.add_middleware(OrderedMiddleware("A"))
    bus.add_middleware(OrderedMiddleware("B"))

    async def handler(event: Event):
        order.append("handler")

    await bus.register(Subscription(topic="test", handler=handler))
    await bus.publish(Event(name="test"))
    await bus.join()

    assert order == ["before_A", "before_B", "after_A", "after_B", "handler"]


async def test_middleware_remove(started_bus):
    bus = started_bus
    recorder = RecordingMiddleware()
    bus.add_middleware(recorder)
    assert bus.remove_middleware(recorder) is True
    assert bus.remove_middleware(recorder) is False

    async def handler(event: Event):
        pass

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()

    assert len(recorder.before_calls) == 0


async def test_middleware_clear_via_clear(started_bus):
    """bus.clear() should also clear middleware list."""
    bus = started_bus
    recorder = RecordingMiddleware()
    bus.add_middleware(recorder)
    bus.clear()

    async def handler(event: Event):
        pass

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()

    assert len(recorder.before_calls) == 0


async def test_base_middleware_defaults():
    """BaseMiddleware provides no-op defaults for all hooks."""
    mw = BaseMiddleware()
    sub = Subscription(topic="t", handler=lambda e: None)
    event = Event(name="test")

    result = await mw.before_publish(event)
    assert result is event

    await mw.after_publish(event)

    result = await mw.before_dispatch(event)
    assert result is event

    result = await mw.before_handler(sub, event)
    assert result is event

    await mw.after_handler(sub, event)

    await mw.on_exception(sub, event, ValueError("x"))

    await mw.after_dispatch(event)


async def test_middleware_protocol():
    """Middleware inheriting BaseMiddleware satisfies EventMiddleware protocol."""
    mw = RecordingMiddleware()
    assert isinstance(mw, EventMiddleware)


async def test_broken_before_middleware_does_not_enqueue(started_bus):
    """If before_publish raises, the event is NOT enqueued."""
    bus = started_bus
    bus.add_middleware(BrokenBeforeMiddleware())

    received = []

    async def handler(event: Event):
        received.append(event.name)

    await bus.register(Subscription(topic="test", handler=handler))

    with pytest.raises(RuntimeError, match="before_publish failed"):
        await bus.publish(Event(name="test"))

    await bus.join()
    assert len(received) == 0
    assert bus.queue_size() == 0


async def test_middleware_chain_rejection_stops_later_middleware(started_bus):
    """If earlier middleware rejects, later middleware before_publish does not run."""
    bus = started_bus

    class DontRunMiddleware:
        def __init__(self) -> None:
            self.ran = False

        async def before_publish(self, event: Event) -> Event:
            self.ran = True
            return event

        async def after_publish(self, event: Event) -> None:
            pass

    dont_run = DontRunMiddleware()
    bus.add_middleware(RejectingMiddleware())
    bus.add_middleware(dont_run)

    with pytest.raises(ValueError, match="not allowed"):
        await bus.publish(Event(name="bad"))

    assert dont_run.ran is False


async def test_failing_after_middleware_still_enqueues(started_bus):
    """An exception in after_publish does NOT undo the enqueue (event already queued)."""
    bus = started_bus
    bus.add_middleware(FailingAfterMiddleware())

    received = []

    async def handler(event: Event):
        received.append(event.name)

    await bus.register(Subscription(topic="test", handler=handler))

    with pytest.raises(RuntimeError, match="after_publish failed"):
        await bus.publish(Event(name="test"))

    await bus.join()
    assert len(received) == 1


async def test_before_dispatch_hook_modifies_event(started_bus):
    """before_dispatch can transform the event before subscriber resolution."""
    bus = started_bus

    class BeforeDispatchMiddleware(BaseMiddleware):
        async def before_dispatch(self, event: Event) -> Event:
            payload = {**(event.payload or {}), "enriched": True}
            return Event(
                name=event.name,
                payload=payload,
                source=event.source,
                correlation_id=event.correlation_id,
                version=event.version,
                timestamp=event.timestamp,
            )

    bus.add_middleware(BeforeDispatchMiddleware())
    received = []

    async def handler(event: Event):
        received.append(event.payload)

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t", payload={"key": "val"}))
    await bus.join()

    assert received == [{"key": "val", "enriched": True}]


async def test_before_handler_per_subscriber(started_bus):
    """before_handler is called per subscriber and can modify the event."""
    bus = started_bus
    events_seen = []

    class BeforeHandlerMiddleware(BaseMiddleware):
        async def before_handler(
            self,
            subscription: Subscription,
            event: Event,
        ) -> Event:
            events_seen.append((subscription.topic, event.name))
            return Event(
                name=event.name,
                payload={**event.payload, "per_sub": subscription.topic},
                source=event.source,
                correlation_id=event.correlation_id,
                version=event.version,
                timestamp=event.timestamp,
            )

    bus.add_middleware(BeforeHandlerMiddleware())
    received = []

    async def handler(event: Event):
        received.append(event.payload)

    await bus.register(Subscription(topic="a", handler=handler))
    await bus.register(
        Subscription(topic="*", handler=handler, priority=200),
    )
    await bus.publish(Event(name="a", payload={"base": True}))
    await bus.join()

    assert len(events_seen) == 2
    assert received == [
        {"base": True, "per_sub": "a"},
        {"base": True, "per_sub": "*"},
    ]


async def test_after_handler_on_success(started_bus):
    """after_handler is called after a successful handler execution."""
    bus = started_bus
    called = []

    class AfterHandlerMiddleware(BaseMiddleware):
        async def after_handler(
            self,
            subscription: Subscription,
            event: Event,
        ) -> None:
            called.append((subscription.topic, event.name))

    bus.add_middleware(AfterHandlerMiddleware())

    async def handler(event: Event):
        pass

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()

    assert called == [("t", "t")]


async def test_on_exception_called_on_handler_failure(started_bus):
    """on_exception is called when a handler raises a retryable exception."""
    bus = started_bus
    exceptions = []

    class OnExceptionMiddleware(BaseMiddleware):
        async def on_exception(
            self,
            subscription: Subscription,
            event: Event,
            exception: Exception,
        ) -> None:
            exceptions.append((subscription.topic, type(exception).__name__))

    bus.add_middleware(OnExceptionMiddleware())

    async def handler(event: Event):
        raise ValueError("boom")

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()

    assert len(exceptions) > 0
    assert exceptions[0] == ("t", "ValueError")


async def test_after_dispatch_called_after_all_subscribers(started_bus):
    """after_dispatch is called once after all subscribers finish."""
    bus = started_bus
    after_dispatch_count = 0

    class AfterDispatchMiddleware(BaseMiddleware):
        async def after_dispatch(self, event: Event) -> None:
            nonlocal after_dispatch_count
            after_dispatch_count += 1

    bus.add_middleware(AfterDispatchMiddleware())

    async def handler(event: Event):
        pass

    await bus.register(Subscription(topic="a", handler=handler))
    await bus.register(Subscription(topic="b", handler=handler))
    await bus.publish(Event(name="a"))
    await bus.join()

    assert after_dispatch_count == 1


async def test_full_lifecycle_order(started_bus):
    """All hooks execute in the correct order."""
    bus = started_bus
    order = []

    class LifecycleMiddleware(BaseMiddleware):
        async def before_publish(self, event: Event) -> Event:
            order.append("before_publish")
            return event

        async def after_publish(self, event: Event) -> None:
            order.append("after_publish")

        async def before_dispatch(self, event: Event) -> Event:
            order.append("before_dispatch")
            return event

        async def before_handler(
            self,
            subscription: Subscription,
            event: Event,
        ) -> Event:
            order.append("before_handler")
            return event

        async def after_handler(
            self,
            subscription: Subscription,
            event: Event,
        ) -> None:
            order.append("after_handler")

        async def after_dispatch(self, event: Event) -> None:
            order.append("after_dispatch")

    bus.add_middleware(LifecycleMiddleware())

    async def handler(event: Event):
        order.append("handler")

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()

    assert order == [
        "before_publish",
        "after_publish",
        "before_dispatch",
        "before_handler",
        "handler",
        "after_handler",
        "after_dispatch",
    ]


async def test_before_handler_rejected_prevents_handler(started_bus):
    """If before_handler raises, the subscriber is not executed."""
    bus = started_bus
    handler_ran = False

    class GuardMiddleware(BaseMiddleware):
        async def before_handler(
            self,
            subscription: Subscription,
            event: Event,
        ) -> Event:
            raise PermissionError("not allowed")

    bus.add_middleware(GuardMiddleware())

    async def handler(event: Event):
        nonlocal handler_ran
        handler_ran = True

    await bus.register(Subscription(topic="t", handler=handler))
    await bus.publish(Event(name="t"))
    await bus.join()

    assert not handler_ran
