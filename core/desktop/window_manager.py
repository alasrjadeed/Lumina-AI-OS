from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass


@dataclass
class WindowInfo:
    id: int
    title: str
    process: str = ""
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    minimized: bool = False
    maximized: bool = False
    focused: bool = False


class WindowManager:
    """List, focus, resize, and manage desktop windows."""

    async def list_windows(self) -> list[WindowInfo]:
        if sys.platform == "linux":
            return await self._list_x11()
        elif sys.platform == "darwin":
            return await self._list_macos()
        return []

    async def focus(self, title_pattern: str) -> bool:
        for w in await self.list_windows():
            if title_pattern.lower() in w.title.lower():
                return await self._focus_window(w.id)
        return False

    async def focus_by_pid(self, pid: int) -> bool:
        for w in await self.list_windows():
            if w.process and str(pid) in w.process:
                return await self._focus_window(w.id)
        return False

    async def resize(self, title_pattern: str, width: int, height: int) -> bool:
        for w in await self.list_windows():
            if title_pattern.lower() in w.title.lower():
                return await self._resize_window(w.id, width, height)
        return False

    async def minimize(self, title_pattern: str) -> bool:
        for w in await self.list_windows():
            if title_pattern.lower() in w.title.lower():
                return await self._minimize_window(w.id)
        return False

    async def maximize(self, title_pattern: str) -> bool:
        for w in await self.list_windows():
            if title_pattern.lower() in w.title.lower():
                return await self._maximize_window(w.id)
        return False

    async def close(self, title_pattern: str) -> bool:
        for w in await self.list_windows():
            if title_pattern.lower() in w.title.lower():
                return await self._close_window(w.id)
        return False

    async def get_active(self) -> WindowInfo | None:
        windows = await self.list_windows()
        for w in windows:
            if w.focused:
                return w
        return None

    async def _list_x11(self) -> list[WindowInfo]:
        try:
            output = subprocess.check_output(
                ["wmctrl", "-lG"],
                timeout=5,
                text=True,
            )
            focused_id = subprocess.check_output(
                ["xdotool", "getactivewindow"],
                timeout=5,
                text=True,
            ).strip()
            windows = []
            for line in output.strip().split("\n"):
                parts = line.split(None, 5)
                if len(parts) >= 6:
                    wid, desktop, x, y, w, h = parts[:6]
                    title = parts[5] if len(parts) > 5 else ""
                    windows.append(
                        WindowInfo(
                            id=int(wid, 16) if wid.startswith("0x") else int(wid),
                            title=title,
                            x=int(x),
                            y=int(y),
                            width=int(w),
                            height=int(h),
                            focused=focused_id == wid,
                        )
                    )
            return windows
        except (FileNotFoundError, subprocess.CalledProcessError):
            return []

    async def _list_macos(self) -> list[WindowInfo]:
        try:
            script = (
                'tell application "System Events"'
                " to get the name of every process whose visible is true"
            )
            output = subprocess.check_output(
                ["osascript", "-e", script],
                timeout=5,
                text=True,
            )
            processes = [p.strip() for p in output.split(",")]
            return [WindowInfo(id=i, title=p) for i, p in enumerate(processes)]
        except (FileNotFoundError, subprocess.CalledProcessError):
            return []

    async def _focus_window(self, window_id: int) -> bool:
        try:
            if sys.platform == "linux":
                subprocess.run(
                    ["xdotool", "windowactivate", str(window_id)],
                    capture_output=True,
                    timeout=5,
                )
            return True
        except Exception:
            return False

    async def _resize_window(self, window_id: int, width: int, height: int) -> bool:
        try:
            if sys.platform == "linux":
                subprocess.run(
                    ["xdotool", "windowsize", str(window_id), str(width), str(height)],
                    capture_output=True,
                    timeout=5,
                )
            return True
        except Exception:
            return False

    async def _minimize_window(self, window_id: int) -> bool:
        try:
            if sys.platform == "linux":
                subprocess.run(
                    ["xdotool", "windowminimize", str(window_id)],
                    capture_output=True,
                    timeout=5,
                )
            return True
        except Exception:
            return False

    async def _maximize_window(self, window_id: int) -> bool:
        try:
            if sys.platform == "linux":
                subprocess.run(
                    [
                        "xdotool",
                        "windowstate",
                        "--add",
                        "maximized_vert,maximized_horz",
                        str(window_id),
                    ],
                    capture_output=True,
                    timeout=5,
                )
            return True
        except Exception:
            return False

    async def _close_window(self, window_id: int) -> bool:
        try:
            if sys.platform == "linux":
                subprocess.run(
                    ["xdotool", "windowclose", str(window_id)],
                    capture_output=True,
                    timeout=5,
                )
            return True
        except Exception:
            return False
