from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

from core.android.device import AndroidDevice
from core.log import log


@dataclass
class AndroidNotification:
    package: str
    title: str
    text: str
    key: str = ""
    timestamp: float = field(default_factory=time.time)
    priority: int = 0
    dismissed: bool = False


class AndroidNotificationManager:
    """Monitor, capture, and send Android device notifications."""

    def __init__(self, device: AndroidDevice | None = None):
        self.device = device or AndroidDevice()
        self._notifications: list[AndroidNotification] = []
        self._max_history = 200
        self._monitoring = False

    def get_active(self) -> list[AndroidNotification]:
        output = self.device.shell("dumpsys notification --noredact 2>/dev/null || "
                                   "dumpsys notification 2>/dev/null")
        notifications = []
        current_pkg = ""
        current_title = ""
        current_text = ""
        for line in output.split("\n"):
            pkg_match = re.match(r"\s+NotificationRecord\(0x[0-9a-f]+\)\s+package=(.+?)\s", line)
            if pkg_match:
                if current_pkg:
                    notifications.append(AndroidNotification(
                        package=current_pkg, title=current_title, text=current_text,
                    ))
                current_pkg = pkg_match.group(1)
                current_title = ""
                current_text = ""
            title_match = re.search(r'title\s*=\s*(.+?)(?:,|$)', line)
            if title_match:
                current_title = title_match.group(1).strip()
            text_match = re.search(r'text\s*=\s*(.+?)(?:,|$)', line)
            if text_match:
                current_text = text_match.group(1).strip()
        if current_pkg:
            notifications.append(AndroidNotification(
                package=current_pkg, title=current_title, text=current_text,
            ))
        return notifications

    def get_history(self, limit: int = 50) -> list[AndroidNotification]:
        return self._notifications[-limit:]

    def get_by_package(self, package: str, limit: int = 20) -> list[AndroidNotification]:
        return [n for n in reversed(self._notifications) if n.package == package][:limit]

    # ── Monitoring via logcat ──

    def start_monitoring(self) -> None:
        self._monitoring = True
        log.info("Notification monitoring started")

    def stop_monitoring(self) -> None:
        self._monitoring = False

    def poll_notifications(self, max_polls: int = 1) -> list[AndroidNotification]:
        new_notifs = []
        if not self.device.is_connected:
            return new_notifs
        try:
            output = self.device.shell("logcat -d -t 100 2>/dev/null")
            for line in output.split("\n"):
                notif_match = re.search(
                    r"notif.*?(?:title|text)[=:]\s*[\"']?(.+?)[\"']?\s*(?:,|$)",
                    line, re.IGNORECASE,
                )
                if notif_match:
                    notification = AndroidNotification(
                        package="system",
                        title="",
                        text=notif_match.group(1)[:200],
                    )
                    self._notifications.append(notification)
                    if len(self._notifications) > self._max_history:
                        self._notifications = self._notifications[-self._max_history:]
                    new_notifs.append(notification)
        except Exception:
            pass
        return new_notifs

    # ── Send notifications to device ──

    def send(self, title: str, message: str, package: str = "com.lumina.app") -> bool:
        try:
            escaped_title = title.replace("'", "\\'")
            escaped_msg = message.replace("'", "\\'")
            cmd = (
                f"am broadcast -a com.lumina.NOTIFY "
                f"-e title '{escaped_title}' -e message '{escaped_msg}'"
            )
            self.device.shell(cmd)
            self._notifications.append(AndroidNotification(
                package=package, title=title, text=message,
            ))
            log.info("Notification sent to device: %s", title)
            return True
        except Exception as e:
            log.error("Failed to send notification: %s", e)
            return False

    def send_alert(self, title: str, message: str) -> bool:
        return self.send(title, message)

    def send_silent(self, title: str, message: str) -> bool:
        return self.send(title, message)

    def clear_history(self) -> None:
        self._notifications.clear()

    def count(self) -> int:
        return len(self._notifications)
