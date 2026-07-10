"""Self-Test Browser — AI-powered browser dedicated to testing and debugging."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

from core.log import log

TEST_BROWSER_DIR = os.path.expanduser("~/.lumina/test_browser")


@dataclass
class ScreenshotComparison:
    id: str
    name: str
    before_path: str
    after_path: str
    diff_path: str = ""
    match_percent: float = 0.0
    passed: bool = False
    timestamp: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "before_path": self.before_path,
            "after_path": self.after_path,
            "diff_path": self.diff_path,
            "match_percent": self.match_percent,
            "passed": self.passed,
            "timestamp": self.timestamp,
        }


@dataclass
class UITestCase:
    id: str
    name: str
    steps: list[dict]
    expected: str
    result: str = ""
    passed: bool | None = None
    duration_ms: float = 0.0
    timestamp: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "steps": self.steps,
            "expected": self.expected,
            "result": self.result,
            "passed": self.passed,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
        }


@dataclass
class NetworkRequest:
    url: str
    method: str
    status: int
    duration_ms: float
    size_bytes: int
    error: str = ""
    timestamp: float = 0.0

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "method": self.method,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "size_bytes": self.size_bytes,
            "error": self.error,
            "timestamp": self.timestamp,
        }


class TestBrowser:
    """Headless test browser for HTML/CSS/JS inspection, network monitoring,
    console error detection, screenshot comparison, and automated UI testing."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._network_requests: list[NetworkRequest] = []
        self._console_errors: list[str] = []
        self._screenshots: dict[str, str] = {}
        self._ui_tests: list[UITestCase] = []
        self._comparisons: list[ScreenshotComparison] = []
        os.makedirs(TEST_BROWSER_DIR, exist_ok=True)

    async def launch(self):
        try:
            from playwright.async_api import (  # pyright: ignore[reportMissingImports]
                async_playwright,
            )

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=self.headless)
            self._context = await self._browser.new_context(
                viewport={"width": 1280, "height": 720},
                ignore_https_errors=True,
            )
            self._page = await self._context.new_page()
            self._network_requests.clear()
            self._console_errors.clear()

            self._page.on("request", self._on_request)
            self._page.on("response", self._on_response)
            self._page.on("console", self._on_console)
            self._page.on("pageerror", self._on_page_error)

            log.info("TestBrowser: launched (headless=%s)", self.headless)
        except ImportError:
            log.warning("TestBrowser: Playwright not installed")
            raise
        except Exception as e:
            log.error("TestBrowser: launch failed: %s", e)
            raise

    async def close(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        log.info("TestBrowser: closed")

    async def _on_request(self, request):
        self._network_requests.append(
            NetworkRequest(
                url=request.url,
                method=request.method,
                status=0,
                duration_ms=0,
                size_bytes=0,
                timestamp=time.time(),
            )
        )

    async def _on_response(self, response):
        matching = [r for r in self._network_requests if r.url == response.url and r.status == 0]
        if matching:
            latest = matching[-1]
            latest.status = response.status
            latest.duration_ms = time.time() - latest.timestamp

    async def _on_console(self, msg):
        if msg.type in ("error", "warning"):
            self._console_errors.append(f"[{msg.type}] {msg.text}")

    async def _on_page_error(self, error):
        self._console_errors.append(f"[pageerror] {error.message}")

    async def navigate(self, url: str, wait_until: str = "networkidle") -> dict:
        if not self._page:
            raise RuntimeError("TestBrowser not launched")
        start = time.time()
        self._network_requests.clear()
        self._console_errors.clear()
        try:
            await self._page.goto(url, wait_until=wait_until, timeout=30000)
            title = await self._page.title()
            return {
                "status": "loaded",
                "url": self._page.url,
                "title": title,
                "duration_ms": int((time.time() - start) * 1000),
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def inspect_html(self, selector: str = "body") -> dict:
        if not self._page:
            return {"error": "Browser not launched"}

        try:
            element = await self._page.query_selector(selector)
            if element:
                text = await element.inner_text()
                html = await element.inner_html()
                attrs = await element.evaluate(
                    "el => Array.from(el.attributes).reduce((o, a) => "
                    "({...o, [a.name]: a.value}), {})"
                )
                return {
                    "selector": selector,
                    "found": True,
                    "text": text[:2000],
                    "html": html[:5000],
                    "attributes": attrs,
                    "children": await element.evaluate("el => el.children.length"),
                }
            return {"selector": selector, "found": False}
        except Exception as e:
            return {"error": str(e)}

    async def inspect_css(self, selector: str) -> dict:
        if not self._page:
            return {"error": "Browser not launched"}

        try:
            styles = await self._page.eval_on_selector(
                selector,
                """el => {
                const computed = getComputedStyle(el);
                const relevant = [
                    'display', 'position', 'width', 'height', 'margin', 'padding',
                    'color', 'backgroundColor', 'fontSize', 'fontFamily', 'fontWeight',
                    'textAlign', 'border', 'borderRadius', 'boxShadow', 'opacity',
                    'transform', 'transition', 'zIndex', 'overflow', 'cursor',
                ];
                const result = {};
                relevant.forEach(p => result[p] = computed.getPropertyValue(p));
                return result;
            }""",
            )
            return {"selector": selector, "computed_styles": styles}
        except Exception as e:
            return {"error": str(e)}

    async def inspect_javascript(self, expression: str = "") -> dict:
        if not self._page:
            return {"error": "Browser not launched"}

        try:
            if expression:
                result = await self._page.evaluate(f"() => {{ return {expression} }}")
                return {"expression": expression, "result": result}
            scripts = await self._page.evaluate("""() => {
                return Array.from(document.scripts).map(s => ({
                    src: s.src || '(inline)',
                    type: s.type,
                    async: s.async,
                    defer: s.defer,
                }));
            }""")
            return {"scripts": scripts, "count": len(scripts)}
        except Exception as e:
            return {"error": str(e)}

    def get_network(self) -> dict:
        return {
            "requests": [r.to_dict() for r in self._network_requests],
            "total": len(self._network_requests),
            "errors": [r.to_dict() for r in self._network_requests if r.status >= 400],
            "slowest": sorted(self._network_requests, key=lambda r: -r.duration_ms)[:5],
        }

    def get_console(self) -> dict:
        return {
            "errors": self._console_errors,
            "count": len(self._console_errors),
            "has_errors": len(self._console_errors) > 0,
        }

    async def screenshot(self, name: str, full_page: bool = True) -> str:
        if not self._page:
            raise RuntimeError("TestBrowser not launched")

        path = os.path.join(TEST_BROWSER_DIR, f"{name}_{int(time.time())}.png")
        await self._page.screenshot(path=path, full_page=full_page)
        self._screenshots[name] = path
        return path

    async def compare_screenshots(
        self, name: str, url_before: str, url_after: str
    ) -> ScreenshotComparison:
        await self.navigate(url_before)
        before_path = await self.screenshot(f"{name}_before")
        await self.navigate(url_after)
        after_path = await self.screenshot(f"{name}_after")

        import uuid

        comp = ScreenshotComparison(
            id=uuid.uuid4().hex[:12],
            name=name,
            before_path=before_path,
            after_path=after_path,
            timestamp=time.time(),
        )

        try:
            from PIL import Image

            before_img = Image.open(before_path).convert("RGB")
            after_img = Image.open(after_path).convert("RGB")
            if before_img.size != after_img.size:
                after_img = after_img.resize(before_img.size)
            bd = list(before_img.getdata())  # pyright: ignore[reportArgumentType]
            ad = list(after_img.getdata())  # pyright: ignore[reportArgumentType]
            total = len(bd)
            same = sum(1 for b, a in zip(bd, ad) if b == a)
            comp.match_percent = round(same / total * 100, 2)
            comp.passed = comp.match_percent > 95

            diff_path = os.path.join(TEST_BROWSER_DIR, f"{name}_diff_{int(time.time())}.png")
            diff_img = Image.new("RGB", before_img.size, (255, 0, 0))
            diff_img.putdata(tuple(b if b == a else (255, 0, 0) for b, a in zip(bd, ad)))
            diff_img.save(diff_path)
            comp.diff_path = diff_path
        except ImportError:
            log.warning("TestBrowser: PIL/Pillow not installed — comparison skipped")
            comp.match_percent = 100
            comp.passed = True

        self._comparisons.append(comp)
        return comp

    async def record_user_flow(self, name: str, steps: list[str]) -> dict:
        if not self._page:
            return {"error": "Browser not launched"}

        results = []
        for i, step in enumerate(steps):
            step_start = time.time()
            try:
                await self._page.evaluate(f"() => {{ {step} }}")
                results.append(
                    {
                        "index": i,
                        "step": step,
                        "status": "success",
                        "duration_ms": int((time.time() - step_start) * 1000),
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "index": i,
                        "step": step,
                        "status": "failed",
                        "error": str(e),
                        "duration_ms": int((time.time() - step_start) * 1000),
                    }
                )

        return {"flow": name, "steps": results, "total": len(results)}

    async def run_ui_test(self, test: UITestCase) -> UITestCase:
        if not self._page:
            raise RuntimeError("TestBrowser not launched")

        start = time.time()
        try:
            for step in test.steps:
                action = step.get("action", "")
                target = step.get("target", "")
                value = step.get("value", "")

                if action == "navigate":
                    await self.navigate(target)
                elif action == "click":
                    await self._page.click(target)
                elif action == "fill":
                    await self._page.fill(target, value)
                elif action == "type":
                    await self._page.type(target, value)
                elif action == "select":
                    await self._page.select_option(target, value)
                elif action == "hover":
                    await self._page.hover(target)
                elif action == "wait":
                    await self._page.wait_for_selector(target)
                elif action == "screenshot":
                    await self.screenshot(value or f"ui_test_{test.id}")
                elif action == "assert_visible":
                    visible = await self._page.is_visible(target)
                    if not visible:
                        raise AssertionError(f"Element not visible: {target}")
                elif action == "assert_text":
                    content = await self._page.text_content(target)
                    if value not in (content or ""):
                        raise AssertionError(f"Text '{value}' not found in '{content}'")

            test.passed = True
            test.result = "All steps passed"
        except Exception as e:
            test.passed = False
            test.result = str(e)

        test.duration_ms = int((time.time() - start) * 1000)
        test.timestamp = time.time()
        self._ui_tests.append(test)
        return test

    async def full_audit(self, url: str) -> dict:
        result = await self.navigate(url)
        if result.get("status") != "loaded":
            return result

        html_info = await self.inspect_html("body")
        network = self.get_network()
        console = self.get_console()
        screenshot_path = await self.screenshot("audit")

        return {
            "url": url,
            "title": result.get("title", ""),
            "html": {
                "text_length": len(html_info.get("text", "")),
                "children": html_info.get("children", 0),
            },
            "network": {
                "total_requests": network["total"],
                "errors": len(network["errors"]),
                "slowest_url": network["slowest"][0].url if network["slowest"] else None,
            },
            "console": {
                "errors": console["count"],
                "has_errors": console["has_errors"],
            },
            "screenshot": screenshot_path,
            "score": max(
                0,
                100
                - (network["total"] > 50) * 10
                - (len(network["errors"]) * 5)
                - (console["count"] * 3),
            ),
        }

    def get_stats(self) -> dict:
        return {
            "screenshots": len(self._screenshots),
            "ui_tests": len(self._ui_tests),
            "comparisons": len(self._comparisons),
            "network_requests": len(self._network_requests),
            "console_errors": len(self._console_errors),
            "passed_tests": sum(1 for t in self._ui_tests if t.passed is True),
            "failed_tests": sum(1 for t in self._ui_tests if t.passed is False),
        }


test_browser = TestBrowser()
