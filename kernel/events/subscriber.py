from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Optional
from uuid import uuid4


HandlerFunc = Callable[..., Coroutine[Any, Any, None]]


@dataclass
class Subscriber:
    handler: HandlerFunc
    name: str = field(default_factory=lambda: f"subscriber_{uuid4().hex[:8]}")
    priority: int = 0
    once: bool = False
    filter_func: Optional[Callable[..., bool]] = None
    id: str = field(default_factory=lambda: uuid4().hex)
    metadata: Optional[dict] = None

    async def handle(self, event) -> None:
        if self.filter_func and not self.filter_func(event):
            return
        await self.handler(event)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Subscriber):
            return self.id == other.id
        return NotImplemented
