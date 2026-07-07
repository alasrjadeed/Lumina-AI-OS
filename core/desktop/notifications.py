from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass, field

try:
    from plyer import notification as plyer_notification
except ImportError:
    plyer_notification = None

from core.log import log


@dataclass
class Notification:
    title: str
    message: str
    level: str = "info"
    timestamp: float = field(default_factory=time.time)
    dismissed: bool = False


class NotificationManager:
    """Send and track desktop notifications."""

    def __init__(self):
        self._history: list[Notification] = []
        self._max_history = 100

    async def send(self, title: str, message: str, level: str = "info") -> bool:
        try:
            self._notify(title, message, level)
            notif = Notification(title=title, message=message, level=level)
            self._history.append(notif)
            if len(self._history) > self._max_history:
                self._history.pop(0)
            log.info("Notification: %s - %s", title, message[:50])
            return True
        except Exception as e:
            log.error("Notification failed: %s", e)
            return False

    async def info(self, title: str, message: str) -> bool:
        return await self.send(title, message, "info")

    async def warn(self, title: str, message: str) -> bool:
        return await self.send(title, message, "warning")

    async def error(self, title: str, message: str) -> bool:
        return await self.send(title, message, "error")

    async def success(self, title: str, message: str) -> bool:
        return await self.send(title, message, "success")

    def get_history(self, level: str = "", limit: int = 20) -> list[Notification]:
        result = self._history
        if level:
            result = [n for n in result if n.level == level]
        return result[-limit:]

    def clear_history(self) -> None:
        self._history.clear()

    def _notify(self, title: str, message: str, level: str) -> None:
        if sys.platform == "darwin":
            subtitle = f" [{level.upper()}]" if level != "info" else ""
            script = f'display notification "{message}" with title "{title}{subtitle}"'
            subprocess.run(["osascript", "-e", script], capture_output=True)
        elif sys.platform == "win32":
            if plyer_notification:
                plyer_notification.notify(title=title, message=message, timeout=5)
            else:
                log.warning("plyer not installed, skipping notification")
        else:
            try:
                subprocess.run(
                    ["notify-send", title, message, "-u", level],
                    capture_output=True,
                    timeout=5,
                )
            except FileNotFoundError:
                log.warning("notify-send not available, skipping notification")
