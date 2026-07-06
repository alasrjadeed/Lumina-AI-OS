"""
Lumina AI
Subscription Model
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Awaitable, Callable
from uuid import UUID, uuid4

from kernel.events.event import Event
from kernel.events.filters import EventFilter

EventHandler = Callable[[Event], Awaitable[None]]


@dataclass(slots=True)
class Subscription:
    """
    Represents one subscription in the Event Bus.
    """

    topic: str

    handler: EventHandler

    priority: int = 100

    enabled: bool = True

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC),
    )

    subscription_id: UUID = field(
        default_factory=uuid4,
    )

    filters: list[EventFilter] = field(
        default_factory=list,
    )
