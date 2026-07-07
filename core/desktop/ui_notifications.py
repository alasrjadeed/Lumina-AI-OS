from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NotificationSeverity(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class UINotification:
    id: str
    title: str
    message: str
    severity: NotificationSeverity = NotificationSeverity.INFO
    timeout: float = 5.0
    timestamp: float = field(default_factory=time.time)
    dismissed: bool = False
    action: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        if self.timeout <= 0:
            return False
        return time.time() - self.timestamp > self.timeout

    @property
    def icon(self) -> str:
        return {
            NotificationSeverity.INFO: "ℹ",
            NotificationSeverity.SUCCESS: "✓",
            NotificationSeverity.WARNING: "⚠",
            NotificationSeverity.ERROR: "✗",
        }.get(self.severity, "ℹ")


NotificationCallback = Callable[[UINotification], None]


class UINotificationManager:
    """In-app toast notification system."""

    def __init__(self, max_visible: int = 5):
        self.max_visible = max_visible
        self._notifications: list[UINotification] = []
        self._counter: int = 0
        self._on_show: NotificationCallback | None = None
        self._on_dismiss: NotificationCallback | None = None

    def notify(
        self,
        title: str,
        message: str,
        severity: NotificationSeverity | str = NotificationSeverity.INFO,
        timeout: float = 5.0,
        action: str = "",
    ) -> UINotification:
        if isinstance(severity, str):
            severity = NotificationSeverity(severity)
        self._counter += 1
        notif = UINotification(
            id=f"notif_{self._counter}",
            title=title,
            message=message,
            severity=severity,
            timeout=timeout,
            action=action,
        )
        self._notifications.append(notif)
        if self._on_show:
            self._on_show(notif)
        self._trim_excess()
        return notif

    def dismiss(self, notif_id: str) -> bool:
        for notif in self._notifications:
            if notif.id == notif_id:
                notif.dismissed = True
                if self._on_dismiss:
                    self._on_dismiss(notif)
                return True
        return False

    def dismiss_all(self) -> int:
        count = 0
        for notif in self._notifications:
            if not notif.dismissed:
                notif.dismissed = True
                count += 1
        return count

    def get_active(self) -> list[UINotification]:
        return [
            n for n in self._notifications
            if not n.dismissed and not n.is_expired
        ][-self.max_visible:]

    def get_all(self) -> list[UINotification]:
        return list(self._notifications)

    def get_unread_count(self) -> int:
        return len([n for n in self._notifications if not n.dismissed])

    def clear_expired(self) -> int:
        before = len(self._notifications)
        self._notifications = [n for n in self._notifications if not n.is_expired]
        return before - len(self._notifications)

    def clear_all(self) -> None:
        self._notifications.clear()

    def info(self, title: str, message: str, timeout: float = 5.0) -> UINotification:
        return self.notify(title, message, NotificationSeverity.INFO, timeout)

    def success(self, title: str, message: str, timeout: float = 5.0) -> UINotification:
        return self.notify(title, message, NotificationSeverity.SUCCESS, timeout)

    def warning(self, title: str, message: str, timeout: float = 8.0) -> UINotification:
        return self.notify(title, message, NotificationSeverity.WARNING, timeout)

    def error(self, title: str, message: str, timeout: float = 0.0) -> UINotification:
        return self.notify(title, message, NotificationSeverity.ERROR, timeout)

    def on_show(self, callback: NotificationCallback) -> None:
        self._on_show = callback

    def on_dismiss(self, callback: NotificationCallback) -> None:
        self._on_dismiss = callback

    def _trim_excess(self) -> None:
        if len(self._notifications) > self.max_visible * 2:
            self._notifications = self._notifications[-self.max_visible * 2:]
