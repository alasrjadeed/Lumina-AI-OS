from __future__ import annotations

import ctypes
import subprocess
import sys

from core.log import log


class ClipboardManager:
    """Read and write system clipboard."""

    def __init__(self):
        self._history: list[str] = []
        self._max_history = 50

    async def copy(self, text: str) -> bool:
        try:
            self._set_clipboard(text)
            self._history.append(text)
            if len(self._history) > self._max_history:
                self._history.pop(0)
            log.info("Clipboard: copied %d chars", len(text))
            return True
        except Exception as e:
            log.error("Clipboard copy failed: %s", e)
            return False

    async def paste(self) -> str:
        try:
            text = self._get_clipboard()
            return text
        except Exception as e:
            log.error("Clipboard paste failed: %s", e)
            return ""

    async def append(self, text: str, separator: str = "\n") -> bool:
        current = await self.paste()
        return await self.copy(current + separator + text if current else text)

    async def clear(self) -> bool:
        return await self.copy("")

    def get_history(self, limit: int = 10) -> list[str]:
        return self._history[-limit:]

    def clear_history(self) -> None:
        self._history.clear()

    def _set_clipboard(self, text: str) -> None:
        if sys.platform == "darwin":
            proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            proc.communicate(text.encode("utf-8"))
        elif sys.platform == "win32":
            proc = subprocess.Popen(["clip"], stdin=subprocess.PIPE)
            proc.communicate(text.encode("utf-8"))
        else:
            proc = subprocess.Popen(
                ["xclip", "-selection", "clipboard"],
                stdin=subprocess.PIPE,
            )
            proc.communicate(text.encode("utf-8"))

    def _get_clipboard(self) -> str:
        if sys.platform == "darwin":
            return subprocess.check_output(["pbpaste"]).decode("utf-8")
        elif sys.platform == "win32":
            ctypes.windll.user32.OpenClipboard(0)
            ctypes.windll.user32.GetClipboardData(1)
            ctypes.windll.user32.CloseClipboard()
            return ""
        else:
            return subprocess.check_output(
                ["xclip", "-selection", "clipboard", "-o"],
            ).decode("utf-8")
