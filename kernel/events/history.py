"""
Lumina AI
Event History
"""

from __future__ import annotations

from collections import deque
from collections.abc import Awaitable, Callable, Iterable

from kernel.events.event import Event

ReplayHandler = Callable[[Event], Awaitable[None]]


class EventHistory:
    """
    In-memory event history with configurable retention.

    Future versions may be backed by:
    - SQLite
    - PostgreSQL
    - Redis
    """

    def __init__(self, max_events: int = 10000) -> None:
        self._events: deque[Event] = deque(maxlen=max_events)

    def store(self, event: Event) -> None:
        """
        Store an event.
        """
        self._events.append(event)

    def all(self) -> list[Event]:
        """
        Return all stored events.
        """
        return list(self._events)

    def count(self) -> int:
        """
        Number of stored events.
        """
        return len(self._events)

    def latest(self, limit: int = 10) -> list[Event]:
        """
        Return the newest events.
        """
        if limit <= 0:
            return []

        return list(self._events)[-limit:]

    def clear(self) -> None:
        """
        Remove all stored events.
        """
        self._events.clear()

    def by_name(self, name: str) -> list[Event]:
        """
        Find events by name.
        """
        return [
            event
            for event in self._events
            if event.name == name
        ]

    def by_source(self, source: str) -> list[Event]:
        """
        Find events by source.
        """
        return [
            event
            for event in self._events
            if event.source == source
        ]

    # ------------------------------------------------------------------
    # Replay
    # ------------------------------------------------------------------

    @staticmethod
    def _as_replay(event: Event) -> Event:
        """
        Return a copy of the event with ``is_replay=True``.

        This prevents replayed events from being stored again
        and avoids infinite replay loops.
        """
        return Event(
            name=event.name,
            payload=event.payload,
            source=event.source,
            correlation_id=event.correlation_id,
            version=event.version,
            is_replay=True,
            timestamp=event.timestamp,
        )

    async def replay(
        self,
        publisher: ReplayHandler,
    ) -> None:
        """
        Replay every stored event in order.
        """
        for event in list(self._events):
            await publisher(self._as_replay(event))

    async def replay_topic(
        self,
        topic: str,
        publisher: ReplayHandler,
    ) -> None:
        """
        Replay events matching a topic.
        """
        for event in list(self._events):
            if event.name == topic:
                await publisher(self._as_replay(event))

    async def replay_source(
        self,
        source: str,
        publisher: ReplayHandler,
    ) -> None:
        """
        Replay events from one source.
        """
        for event in list(self._events):
            if event.source == source:
                await publisher(self._as_replay(event))

    async def replay_where(
        self,
        predicate: Callable[[Event], bool],
        publisher: ReplayHandler,
    ) -> None:
        """
        Replay events that satisfy a predicate.
        """
        for event in list(self._events):
            if predicate(event):
                await publisher(self._as_replay(event))

    def __iter__(self) -> Iterable[Event]:
        return iter(self._events)

    def __len__(self) -> int:
        return len(self._events)
