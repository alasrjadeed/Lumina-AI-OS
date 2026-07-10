from __future__ import annotations

import subprocess
import sys

_HAS_PLYER = False
plyer_notification = None
try:
    from plyer import notification as plyer_notification

    _HAS_PLYER = True
except Exception:
    pass


def notify(title: str, message: str, timeout: int = 5) -> bool:
    if sys.platform == "linux":
        try:
            subprocess.run(
                ["notify-send", title, message, f"-t={timeout * 1000}"],
                capture_output=True,
                timeout=3,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        try:
            subprocess.run(
                ["dunstify", title, message, f"-t={timeout * 1000}"],
                capture_output=True,
                timeout=3,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    if _HAS_PLYER and plyer_notification is not None:
        try:
            plyer_notification.notify(title=title, message=message, timeout=timeout)  # pyright: ignore[reportOptionalCall]
            return True
        except Exception:
            pass
    print(f"[Jarvis] {title}: {message}", flush=True)
    return False
