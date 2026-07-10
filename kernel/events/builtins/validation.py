from __future__ import annotations

from collections.abc import Callable

from kernel.events.event import Event
from kernel.events.exceptions import EventValidationError
from kernel.events.middleware import BaseMiddleware

Validator = Callable[[Event], bool]


class ValidationMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self._validators: dict[str, list[Validator]] = {}

    def add_validator(
        self,
        event_name: str,
        validator: Validator,
    ) -> None:
        self._validators.setdefault(event_name, []).append(validator)

    def remove_validator(
        self,
        event_name: str,
        validator: Validator,
    ) -> bool:
        validators = self._validators.get(event_name)
        if not validators:
            return False
        try:
            validators.remove(validator)
            if not validators:
                del self._validators[event_name]
            return True
        except ValueError:
            return False

    async def before_publish(self, event: Event) -> Event:
        validators = self._validators.get(event.name, [])
        for validator in validators:
            if not validator(event):
                raise EventValidationError(f"Validation failed for event '{event.name}'")
        return event
