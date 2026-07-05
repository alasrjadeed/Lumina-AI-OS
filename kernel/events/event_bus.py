import asyncio
import logging
from collections import defaultdict
from typing import Dict, List, Optional, Set

from kernel.events.event import Event, EventPriority
from kernel.events.subscriber import Subscriber, HandlerFunc

logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, Set[Subscriber]] = defaultdict(set)
        self._history: List[Event] = []
        self._max_history: int = 1000
        self._lock = asyncio.Lock()
        self._running = False

    async def publish(self, event: Event) -> None:
        async with self._lock:
            subscribers = self._subscribers.get(event.name, set()).copy()
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history.pop(0)

        sorted_subs = sorted(subscribers, key=lambda s: s.priority, reverse=True)
        tasks = []
        for sub in sorted_subs:
            tasks.append(self._safe_dispatch(sub, event))
            if sub.once:
                self._subscribers[event.name].discard(sub)

        if tasks:
            await asyncio.gather(*tasks)

    async def _safe_dispatch(self, subscriber: Subscriber, event: Event) -> None:
        try:
            await subscriber.handle(event)
        except Exception:
            logger.exception(f"Error dispatching event {event.name} to {subscriber.name}")

    def subscribe(
        self,
        event_name: str,
        handler: HandlerFunc,
        priority: int = 0,
        once: bool = False,
        filter_func=None,
        name: Optional[str] = None,
    ) -> Subscriber:
        sub = Subscriber(
            handler=handler,
            priority=priority,
            once=once,
            filter_func=filter_func,
            name=name or f"sub_{event_name}_{len(self._subscribers[event_name])}",
        )
        self._subscribers[event_name].add(sub)
        return sub

    def unsubscribe(self, event_name: str, subscriber: Subscriber) -> bool:
        try:
            self._subscribers[event_name].discard(subscriber)
            return True
        except KeyError:
            return False

    def get_subscribers(self, event_name: str) -> Set[Subscriber]:
        return self._subscribers.get(event_name, set()).copy()

    def get_history(self, limit: Optional[int] = None) -> List[Event]:
        if limit:
            return self._history[-limit:]
        return self._history.copy()

    def clear_history(self) -> None:
        self._history.clear()

    def event_count(self, event_name: Optional[str] = None) -> int:
        if event_name:
            return sum(1 for e in self._history if e.name == event_name)
        return len(self._history)
