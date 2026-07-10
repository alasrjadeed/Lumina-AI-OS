"""
Lumina AI Kernel
Core Event Bus
"""

from __future__ import annotations

import asyncio
from asyncio import Queue
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from kernel.events.dead_letter import DeadLetterEntry, DeadLetterQueue
from kernel.events.dlq_backend import DLQBackend
from kernel.events.envelope import EventEnvelope, RetryDecision
from kernel.events.event import Event
from kernel.events.exceptions import (
    DuplicateSubscriberError,
    EventSubscriberError,
    EventValidationError,
)
from kernel.events.history import EventHistory
from kernel.events.metrics import EventBusMetrics
from kernel.events.middleware import EventMiddleware
from kernel.events.retry import RetryPolicy
from kernel.events.subscription import Subscription
from kernel.events.topic_matcher import TopicMatcher

EventHandler = Callable[[Event], Awaitable[RetryDecision | None]]


class EventBus:
    """
    Core asynchronous event bus with a queue-based pipeline.

    Publisher           publish()
        |                  |
        v                  v
    before_publish  ──>  Internal Queue
        |                  |
        v                  v
    after_publish     Dispatch Loop
                           |
                           v
                   Subscriber Execution
    """

    def __init__(
        self,
        retry_policy: RetryPolicy | None = None,
        container: Any | None = None,
    ) -> None:
        self._container = container
        self._subscriptions: dict[str, list[Subscription]] = defaultdict(list)
        self._queue: Queue[Event] = Queue()
        self._lock = asyncio.Lock()
        self._dispatch_task: asyncio.Task[None] | None = None
        self._middleware: list[EventMiddleware] = []
        self._history = EventHistory()
        self._retry_policy = retry_policy or RetryPolicy()
        self._metrics = EventBusMetrics()
        self._dead_letters = DeadLetterQueue()
        self._running = True

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def metrics(self) -> EventBusMetrics:
        """Return live metrics."""
        self._metrics.queue_depth = self._queue.qsize()
        return self._metrics

    # ------------------------------------------------------------------
    # Middleware
    # ------------------------------------------------------------------

    def resolve_middleware(
        self,
        service_type: type,
    ) -> EventMiddleware | None:
        if self._container is None:
            return None
        try:
            return self._container.resolve(service_type)
        except Exception:
            return None

    def add_middleware(
        self,
        middleware: EventMiddleware,
    ) -> None:
        """Register middleware."""
        self._middleware.append(middleware)

    def remove_middleware(
        self,
        middleware: EventMiddleware,
    ) -> bool:
        """Remove middleware."""
        try:
            self._middleware.remove(middleware)
            return True
        except ValueError:
            return False

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    async def register(
        self,
        subscription: Subscription,
    ) -> None:
        """
        Register a subscription.
        """
        async with self._lock:
            handlers = self._subscriptions[subscription.topic]
            for existing in handlers:
                if existing.handler is subscription.handler:
                    raise DuplicateSubscriberError(subscription.topic)
            handlers.append(subscription)
            handlers.sort(key=lambda x: (x.priority, x.created_at))
        self._metrics.active_subscribers += 1

    async def unregister(
        self,
        topic: str,
        handler: EventHandler,
    ) -> bool:
        """
        Remove a subscription by topic + handler.

        Returns True if removed.
        """
        async with self._lock:
            subscriptions = self._subscriptions.get(topic)
            if subscriptions is None:
                return False
            for sub in subscriptions:
                if sub.handler is handler:
                    subscriptions.remove(sub)
                    if not subscriptions:
                        del self._subscriptions[topic]
                    self._metrics.active_subscribers -= 1
                    return True
            return False

    # ------------------------------------------------------------------
    # Publishing pipeline
    # ------------------------------------------------------------------

    async def publish(
        self,
        event: Event,
    ) -> None:
        """
        Run before-publish middleware, enqueue the event,
        then run after-publish middleware.
        """
        if not self._running:
            raise RuntimeError("EventBus has been shut down.")

        if not event.name:
            raise EventValidationError("Event name cannot be empty")

        for middleware in self._middleware:
            event = await middleware.before_publish(event)

        if not event.is_replay:
            self._history.store(event)

        self._metrics.published_events += 1
        self._metrics.queue_depth = self._queue.qsize()

        await self._queue.put(event)

        for middleware in self._middleware:
            await middleware.after_publish(event)

    async def dispatch(self) -> None:
        """
        Background loop: pull events from the queue and dispatch them.

        Intended to run as ``asyncio.create_task(bus.dispatch())``.
        """
        while self._running or not self._queue.empty():
            try:
                event = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0,
                )
            except TimeoutError:
                continue
            try:
                await self._dispatch_event(event)
            except Exception:
                pass
            finally:
                self._queue.task_done()

    async def _dispatch_event(
        self,
        event: Event,
    ) -> None:
        for mw in self._middleware:
            if hasattr(mw, "before_dispatch"):
                event = await mw.before_dispatch(event)

        subscriptions: list[Subscription] = []
        for topic, handlers in self._subscriptions.items():
            if TopicMatcher.matches(topic, event.name):
                subscriptions.extend(handlers)
        subscriptions.sort(key=lambda x: (x.priority, x.created_at))

        if not subscriptions:
            return

        self._metrics.queue_depth = self._queue.qsize()

        await asyncio.gather(
            *[
                self._execute(
                    sub,
                    EventEnvelope(event=event, replay=event.is_replay),
                )
                for sub in subscriptions
                if sub.enabled and all(f.matches(event) for f in sub.filters)
            ],
        )

        for mw in self._middleware:
            if hasattr(mw, "after_dispatch"):
                await mw.after_dispatch(event)

    async def _execute(
        self,
        subscription: Subscription,
        envelope: EventEnvelope,
    ) -> None:
        event = envelope.event
        for mw in self._middleware:
            if hasattr(mw, "before_handler"):
                event = await mw.before_handler(subscription, event)

        modified = EventEnvelope(event=event, replay=event.is_replay)

        while True:
            try:
                modified.attempts += 1
                result = await subscription.handler(modified.event)
                if isinstance(result, RetryDecision):
                    if result is RetryDecision.IGNORE:
                        return
                    if result in (RetryDecision.FAIL, RetryDecision.DEAD_LETTER):
                        self._metrics.failed_events += 1
                        self._dead_letters.add(
                            DeadLetterEntry(
                                event=modified.event,
                                attempts=modified.attempts,
                                exception="Handler returned " + result.name,
                                exception_type="RetryDecision",
                                subscriber=subscription.handler.__name__,
                            ),
                        )
                        raise EventSubscriberError(f"Handler returned {result.name}")
                self._metrics.dispatched_events += 1

                for mw in self._middleware:
                    if hasattr(mw, "after_handler"):
                        await mw.after_handler(subscription, modified.event)
                return
            except self._retry_policy.retry_exceptions as ex:
                modified.last_error = str(ex)

                decision: RetryDecision | None = None
                for mw in self._middleware:
                    if hasattr(mw, "on_exception"):
                        mw_result = await mw.on_exception(
                            subscription,
                            modified.event,
                            ex,
                        )
                        if isinstance(mw_result, RetryDecision):
                            decision = mw_result

                if decision is RetryDecision.IGNORE:
                    return

                send_to_dlq = (
                    decision is RetryDecision.DEAD_LETTER
                    or decision is RetryDecision.FAIL
                    or modified.attempts >= self._retry_policy.max_attempts
                )
                if send_to_dlq:
                    self._metrics.failed_events += 1
                    self._dead_letters.add(
                        DeadLetterEntry(
                            event=modified.event,
                            attempts=modified.attempts,
                            exception=str(ex),
                            exception_type=type(ex).__name__,
                            subscriber=subscription.handler.__name__,
                        ),
                    )
                    raise EventSubscriberError(str(ex)) from ex
                self._metrics.retried_events += 1
                await asyncio.sleep(
                    self._retry_policy.delay_for_attempt(modified.attempts),
                )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the background dispatch loop."""
        if self._dispatch_task is None or self._dispatch_task.done():
            self._dispatch_task = asyncio.create_task(self.dispatch())

    async def shutdown(self) -> None:
        """
        Gracefully stop accepting new work, drain the queue, and terminate.
        """
        self._running = False
        if self._dispatch_task and not self._dispatch_task.done():
            await self._queue.join()
            self._dispatch_task.cancel()
        self._dispatch_task = None

    async def join(self) -> None:
        """Wait until all queued events have been processed."""
        await self._queue.join()

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def has_subscribers(self, topic: str) -> bool:
        return topic in self._subscriptions

    def subscriber_count(self, topic: str) -> int:
        return len(self._subscriptions.get(topic, []))

    def queue_size(self) -> int:
        """Number of pending events in the queue."""
        return self._queue.qsize()

    def clear(self) -> None:
        self._subscriptions.clear()
        self._middleware.clear()

    def topics(self) -> list[str]:
        return sorted(self._subscriptions.keys())

    def history(self) -> list[Event]:
        """Return all stored events from history."""
        return self._history.all()

    def history_count(self) -> int:
        """Number of stored events in history."""
        return self._history.count()

    def clear_history(self) -> None:
        """Remove all stored events from history."""
        self._history.clear()

    async def replay(self) -> None:
        """
        Replay all stored events through the normal publish pipeline.
        """
        await self._history.replay(self.publish)

    async def replay_topic(self, topic: str) -> None:
        """
        Replay stored events matching a topic through the publish pipeline.
        """
        await self._history.replay_topic(topic, self.publish)

    async def replay_source(self, source: str) -> None:
        """
        Replay stored events from one source through the publish pipeline.
        """
        await self._history.replay_source(source, self.publish)

    async def replay_where(
        self,
        predicate: Callable[[Event], bool],
    ) -> None:
        """
        Replay stored events satisfying a predicate through the publish pipeline.
        """
        await self._history.replay_where(predicate, self.publish)

    async def replay_plugins(self) -> None:
        """
        Replay all plugin.loaded events through the publish pipeline.
        """
        await self._history.replay_topic("plugin.loaded", self.publish)

    # ------------------------------------------------------------------
    # Dead Letter Queue
    # ------------------------------------------------------------------

    def set_dlq_backend(self, backend: DLQBackend) -> None:
        self._dead_letters = backend

    def dead_letter_count(self) -> int:
        return self._dead_letters.count()

    def dead_letters(self) -> list[DeadLetterEntry]:
        return self._dead_letters.all()

    def clear_dead_letters(self) -> None:
        self._dead_letters.clear()

    async def replay_dead_letters(self) -> None:
        entries = self._dead_letters.all()
        self._dead_letters.clear()
        for entry in entries:
            if entry.event is not None:
                await self.publish(entry.event)
