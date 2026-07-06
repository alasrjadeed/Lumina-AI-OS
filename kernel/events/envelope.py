"""
Lumina AI
Event Envelope
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import auto, Enum

from kernel.events.event import Event


class RetryDecision(Enum):
    """
    Decision for a single delivery attempt.

    Future Dead Letter Queue integration will use these to
    route failed events instead of hard-coding logic in
    ``_execute()``.
    """

    RETRY = auto()
    """Retry the delivery (within policy limits)."""

    FAIL = auto()
    """Give up and report the failure."""

    DEAD_LETTER = auto()
    """Route to the dead letter queue."""

    IGNORE = auto()
    """Silently discard the event."""


@dataclass(slots=True)
class EventEnvelope:
    """
    Runtime delivery information.

    Keeps transport metadata out of Event.
    """

    event: Event

    attempts: int = 0

    last_error: str | None = None

    replay: bool = False
