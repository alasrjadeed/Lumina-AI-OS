from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass, field


@dataclass
class ScreenshotInfo:
    path: str
    timestamp: float = field(default_factory=time.time)
    full_page: bool = False
    selector: str = ""
    size: int = 0


class ScreenshotManager:
    """Advanced screenshot capture and comparison."""

    def __init__(self, page, output_dir: str = ".browser_screenshots"):
        self._page = page
        self.output_dir = output_dir
        self._history: list[ScreenshotInfo] = []
        os.makedirs(output_dir, exist_ok=True)

    async def capture(
        self, path: str = "", full_page: bool = True,
        quality: int | None = None,
    ) -> str:
        filename = path or f"screenshot_{int(time.time())}.png"
        if not os.path.isabs(filename):
            filename = os.path.join(self.output_dir, filename)
        await self._page.screenshot(path=filename, full_page=full_page)
        info = ScreenshotInfo(
            path=filename,
            full_page=full_page,
            size=os.path.getsize(filename) if os.path.exists(filename) else 0,
        )
        self._history.append(info)
        return filename

    async def capture_element(self, selector: str, path: str = "") -> str:
        el = await self._page.query_selector(selector)
        if not el:
            raise ValueError(f"Element not found: {selector}")
        filename = path or f"element_{int(time.time())}.png"
        if not os.path.isabs(filename):
            filename = os.path.join(self.output_dir, filename)
        await el.screenshot(path=filename)
        info = ScreenshotInfo(path=filename, full_page=False, selector=selector)
        self._history.append(info)
        return filename

    async def capture_visible(self, path: str = "") -> str:
        return await self.capture(path=path, full_page=False)

    async def batch_capture(self, selectors: list[str], prefix: str = "batch") -> list[str]:
        paths = []
        for i, sel in enumerate(selectors):
            path = os.path.join(self.output_dir, f"{prefix}_{i}.png")
            try:
                result = await self.capture_element(sel, path=path)
                paths.append(result)
            except Exception:
                pass
        return paths

    def compare(self, path1: str, path2: str) -> float:
        h1 = self._hash(path1)
        h2 = self._hash(path2)
        if h1 == h2:
            return 0.0
        diff = sum(1 for a, b in zip(h1, h2) if a != b)
        return diff / len(h1)

    def get_history(self, limit: int = 10) -> list[ScreenshotInfo]:
        return self._history[-limit:]

    def clear_history(self) -> None:
        self._history.clear()

    def _hash(self, path: str) -> str:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
