from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass, field

from core.log import log


@dataclass
class ConsoleEntry:
    level: str
    text: str
    url: str = ""
    line: int = 0
    timestamp: float = field(default_factory=time.time)


@dataclass
class PerformanceMetrics:
    dom_content_loaded: float = 0.0
    load: float = 0.0
    first_paint: float = 0.0
    first_contentful_paint: float = 0.0
    js_heap_size: float = 0.0
    dom_nodes: int = 0
    layout_shift: float = 0.0


class PageMonitor:
    """Monitor page activity — console, performance, mutations, screenshots."""

    def __init__(self, page):
        self._page = page
        self._console_log: list[ConsoleEntry] = []
        self._console_handler = None
        self._mutation_handler = None
        self._screenshot_dir = ".browser_screenshots"
        os.makedirs(self._screenshot_dir, exist_ok=True)

    async def start_console_capture(self) -> None:
        async def on_console(msg):
            entry = ConsoleEntry(
                level=msg.type,
                text=msg.text[:500],
                url=msg.location.get("url", ""),
                line=msg.location.get("lineNumber", 0),
            )
            self._console_log.append(entry)

        self._page.on("console", on_console)
        self._console_handler = on_console

    async def stop_console_capture(self) -> None:
        if self._console_handler:
            self._page.remove_listener("console", self._console_handler)
            self._console_handler = None

    def get_console_log(self, level: str = "") -> list[ConsoleEntry]:
        if level:
            return [e for e in self._console_log if e.level == level]
        return list(self._console_log)

    def clear_console_log(self) -> None:
        self._console_log.clear()

    def has_errors(self) -> bool:
        return any(e.level == "error" for e in self._console_log)

    def has_warnings(self) -> bool:
        return any(e.level == "warning" for e in self._console_log)

    async def get_performance_metrics(self) -> PerformanceMetrics:
        try:
            raw = await self._page.evaluate("""() => {
                const perf = performance.getEntriesByType('navigation')[0] || {};
                const paint = performance.getEntriesByType('paint') || [];
                const fp = paint.find(e => e.name === 'first-paint');
                const fcp = paint.find(e => e.name === 'first-contentful-paint');
                return {
                    domContentLoaded: perf.domContentLoadedEventEnd || 0,
                    load: perf.loadEventEnd || 0,
                    firstPaint: fp ? fp.startTime : 0,
                    firstContentfulPaint: fcp ? fcp.startTime : 0,
                };
            }""")
            js_heap = await self._page.evaluate(
                "performance.memory?.usedJSHeapSize || 0",
            )
            dom_nodes = await self._page.evaluate(
                "document.querySelectorAll('*').length",
            )
            return PerformanceMetrics(
                dom_content_loaded=raw.get("domContentLoaded", 0),
                load=raw.get("load", 0),
                first_paint=raw.get("firstPaint", 0),
                first_contentful_paint=raw.get("firstContentfulPaint", 0),
                js_heap_size=js_heap,
                dom_nodes=dom_nodes,
            )
        except Exception:
            return PerformanceMetrics()

    async def screenshot(self, name: str = "") -> str:
        filename = f"{name or int(time.time())}.png"
        path = os.path.join(self._screenshot_dir, filename)
        await self._page.screenshot(path=path, full_page=True)
        log.info("Screenshot saved: %s", path)
        return path

    async def screenshot_diff(self, name: str = "diff") -> float | None:
        current_path = await self.screenshot("current")
        baseline_path = os.path.join(self._screenshot_dir, f"{name}_baseline.png")
        if not os.path.exists(baseline_path):
            os.rename(current_path, baseline_path)
            return None
        with open(current_path, "rb") as f:
            current_hash = hashlib.md5(f.read()).hexdigest()
        with open(baseline_path, "rb") as f:
            baseline_hash = hashlib.md5(f.read()).hexdigest()
        os.remove(current_path)
        if current_hash == baseline_hash:
            return 0.0
        diff = sum(1 for a, b in zip(current_hash, baseline_hash) if a != b)
        return diff / len(current_hash)

    async def start_mutation_tracking(self) -> None:
        async def on_mutation(entries):
            pass

        await self._page.evaluate("""
            window.__mutationCount = 0;
            window.__observer = new MutationObserver(() => {
                window.__mutationCount++;
            });
            window.__observer.observe(document.body, {
                childList: true,
                subtree: true,
                attributes: true,
                characterData: true,
            });
        """)
        self._mutation_handler = on_mutation

    async def stop_mutation_tracking(self) -> None:
        await self._page.evaluate("window.__observer?.disconnect()")
        self._mutation_handler = None

    async def get_mutation_count(self) -> int:
        try:
            return await self._page.evaluate("window.__mutationCount || 0")
        except Exception:
            return 0

    async def check_accessibility(self) -> list[dict]:
        issues = []
        checks = {
            "missing_alt": "document.querySelectorAll('img:not([alt])').length",
            "missing_label": (
                "document.querySelectorAll('input:not([aria-label]):not([placeholder])').length"
            ),
            "low_contrast_btn": "document.querySelectorAll('button').length",
            "missing_role": "document.querySelectorAll('[role]').length",
        }
        for name, js in checks.items():
            try:
                count = await self._page.evaluate(js)
                if count > 0:
                    issues.append({"type": name, "count": count})
            except Exception:
                pass
        return issues
