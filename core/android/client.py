from __future__ import annotations

import re
import time
from dataclasses import dataclass

from core.android.device import AndroidDevice
from core.log import log


@dataclass
class AppInfo:
    package: str
    name: str = ""
    version: str = ""
    pid: int = 0
    running: bool = False


@dataclass
class ScreenInfo:
    width: int = 0
    height: int = 0
    density: int = 0
    rotation: int = 0


class AndroidClient:
    """Higher-level Android client wrapping AndroidDevice with app mgmt and monitoring."""

    def __init__(self, device: AndroidDevice | None = None):
        self.device = device or AndroidDevice()
        self._screen_info: ScreenInfo | None = None

    def connect(self, serial: str | None = None) -> bool:
        self.device.connect(serial)
        if self.device.is_connected:
            self._screen_info = self._get_screen_info()
            return True
        return False

    def disconnect(self) -> None:
        self.device.disconnect()

    @property
    def is_connected(self) -> bool:
        return self.device.is_connected

    # ── App Management ──

    def app_info(self, package: str) -> AppInfo:
        output = self.device.shell(f"dumpsys package {package} | grep -E 'versionName|versionCode'")
        version = ""
        for line in output.split("\n"):
            if "versionName" in line:
                version = line.split("=")[-1].strip()
        pid_output = self.device.shell(f"pidof {package}").strip()
        pid = int(pid_output) if pid_output.isdigit() else 0
        return AppInfo(package=package, version=version, pid=pid, running=pid > 0)

    def app_launch(self, package: str, activity: str = "") -> bool:
        if not activity:
            activity = self._get_main_activity(package)
            if not activity:
                log.error("No main activity for %s", package)
                return False
        self.device.shell(f"am start -n {package}/{activity}")
        log.info("Launched: %s/%s", package, activity)
        return True

    def app_force_stop(self, package: str) -> None:
        self.device.shell(f"am force-stop {package}")
        log.info("Force stopped: %s", package)

    def app_clear_data(self, package: str) -> None:
        self.device.shell(f"pm clear {package}")
        log.info("Cleared data: %s", package)

    def app_list_running(self) -> list[AppInfo]:
        output = self.device.shell("ps -A -o NAME,PID 2>/dev/null || ps -o NAME,PID")
        apps = []
        for line in output.split("\n"):
            parts = line.strip().split()
            if len(parts) >= 2 and parts[0].startswith("com."):
                apps.append(AppInfo(package=parts[0], pid=int(parts[1]), running=True))
        return apps

    # ── Screen ──

    def _get_screen_info(self) -> ScreenInfo:
        output = self.device.shell("wm size")
        size_match = re.search(r"(\d+)x(\d+)", output)
        width, height = 0, 0
        if size_match:
            width, height = int(size_match.group(1)), int(size_match.group(2))
        density_output = self.device.shell("wm density")
        density_match = re.search(r"(\d+)", density_output)
        density = int(density_match.group(1)) if density_match else 0
        return ScreenInfo(width=width, height=height, density=density)

    def screen_info(self) -> ScreenInfo:
        if not self._screen_info:
            self._screen_info = self._get_screen_info()
        return self._screen_info

    def screenrecord(self, path: str = "/sdcard/record.mp4", duration: int = 30,
                     bit_rate: int = 4000000) -> str:
        self.device.shell(f"screenrecord --time-limit {duration} --bit-rate {bit_rate} {path}")
        log.info("Screen recording saved: %s (%ds)", path, duration)
        return path

    def is_screen_on(self) -> bool:
        output = self.device.shell("dumpsys power | grep 'mHoldingDisplaySuspendBlocker'")
        return "mHoldingDisplaySuspendBlocker=true" in output

    def wake(self) -> None:
        self.device.input_keyevent(26)
        time.sleep(0.5)

    def lock(self) -> None:
        self.device.input_keyevent(26)

    # ── Clipboard ──

    def clipboard_get(self) -> str:
        return self.device.shell("am broadcast -a clipper.get").strip()

    def clipboard_set(self, text: str) -> None:
        escaped = text.replace("'", "\\'")
        self.device.shell(f"am broadcast -a clipper.set -e text '{escaped}'")

    # ── File Management ──

    def file_exists(self, path: str) -> bool:
        output = self.device.shell(f"ls {path} 2>/dev/null && echo EXISTS")
        return "EXISTS" in output

    def file_size(self, path: str) -> int:
        output = self.device.shell(f"stat -c%s {path} 2>/dev/null || echo 0")
        try:
            return int(output.strip().split("\n")[0])
        except ValueError:
            return 0

    def list_dir(self, path: str) -> list[dict]:
        output = self.device.shell(f"ls -la {path} 2>/dev/null")
        items = []
        for line in output.split("\n"):
            parts = line.split()
            if len(parts) >= 9 and parts[0].startswith(("-", "d")):
                items.append({
                    "permissions": parts[0],
                    "size": int(parts[4]) if parts[4].isdigit() else 0,
                    "name": parts[-1],
                    "is_dir": parts[0].startswith("d"),
                })
        return items

    # ── Monitoring ──

    def battery_level(self) -> int:
        output = self.device.shell("dumpsys battery | grep level")
        match = re.search(r"(\d+)", output)
        return int(match.group(1)) if match else 0

    def network_status(self) -> dict:
        output = self.device.shell("dumpsys connectivity | grep 'Active network' -A 2")
        return {"raw": output.strip()[:200]}

    def device_temp(self) -> float:
        output = self.device.shell("dumpsys battery | grep temperature")
        match = re.search(r"(\d+)", output)
        return int(match.group(1)) / 10.0 if match else 0.0

    # ── Helpers ──

    def _get_main_activity(self, package: str) -> str:
        output = self.device.shell(f"cmd package resolve-activity --brief {package} 2>/dev/null "
                                   f"|| dumpsys package {package} | grep -A 1 'MAIN'")
        for line in output.split("\n"):
            line = line.strip()
            if "/" in line and line.startswith(package):
                return line.split()[-1]
        return ""

    def take_screenshot(self, local_path: str = "screenshot.png") -> str:
        remote = "/sdcard/screen_temp.png"
        self.device.screenshot(remote)
        self.device.pull(remote, local_path)
        self.device.shell(f"rm {remote}")
        return local_path
