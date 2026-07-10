from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from kernel.events.event import Event


class EventFilter(ABC):
    @abstractmethod
    def matches(self, event: Event) -> bool: ...


class SourceFilter(EventFilter):
    def __init__(self, source: str) -> None:
        self._source = source

    def matches(self, event: Event) -> bool:
        return event.source == self._source


class NameFilter(EventFilter):
    def __init__(self, name: str) -> None:
        self._name = name

    def matches(self, event: Event) -> bool:
        return event.name == self._name


class PayloadValueFilter(EventFilter):
    def __init__(self, key: str, value: Any) -> None:
        self._key = key
        self._value = value

    def matches(self, event: Event) -> bool:
        return bool(event.payload) and event.payload.get(self._key) == self._value


class PredicateFilter(EventFilter):
    def __init__(self, predicate) -> None:
        self._predicate = predicate

    def matches(self, event: Event) -> bool:
        return self._predicate(event)


class CompositeFilter(EventFilter):
    def __init__(self, *filters: EventFilter) -> None:
        self._filters = filters

    def matches(self, event: Event) -> bool:
        return all(f.matches(event) for f in self._filters)
