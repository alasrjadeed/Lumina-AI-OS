from __future__ import annotations

from typing import Any

from core.browser.dom_interaction import DOMInteraction
from core.browser.downloads import DownloadManager
from core.browser.finder import ElementFinder
from core.browser.monitor import PageMonitor
from core.browser.network import NetworkInterceptor
from core.browser.page import PageInteractor
from core.browser.screenshots import ScreenshotManager
from core.browser.session import SessionManager
from core.browser.tab_manager import TabManager
from core.log import log


class AutomationAPI:
    """Unified high-level automation interface combining all browser modules."""

    def __init__(self, page):
        self._page = page
        self.page = PageInteractor(page)
        self.tabs = TabManager(page)
        self.sessions = SessionManager(page)
        self.network = NetworkInterceptor(page)
        self.finder = ElementFinder(page)
        self.monitor = PageMonitor(page)
        self.screenshots = ScreenshotManager(page)
        self.downloads = DownloadManager(page)
        self.dom = DOMInteraction(page)

    async def navigate(self, url: str, wait_until: str = "networkidle") -> AutomationAPI:
        await self._page.goto(url, wait_until=wait_until)
        log.info("Navigated to: %s", url)
        return self

    async def click(self, selector: str, wait: bool = True) -> AutomationAPI:
        if wait:
            await self.page.wait(selector=selector)
        await self._page.click(selector)
        return self

    async def fill(self, selector: str, value: str) -> AutomationAPI:
        await self._page.fill(selector, value)
        return self

    async def type(self, selector: str, text: str, delay: int = 0) -> AutomationAPI:
        await self._page.type(selector, text, delay=delay)
        return self

    async def select(self, selector: str, value: str | list[str]) -> AutomationAPI:
        await self._page.select_option(selector, value)
        return self

    async def extract_text(self, selector: str) -> str:
        return await self._page.inner_text(selector)

    async def extract_html(self, selector: str = "") -> str:
        if selector:
            el = await self._page.query_selector(selector)
            return await el.inner_html() if el else ""
        return await self._page.content()

    async def extract_links(self) -> list[dict]:
        return await self._page.eval_on_selector_all(
            "a[href]",
            "els => els.map(el => ({ text: el.innerText.trim(), href: el.href }))",
        )

    async def wait_for_page(self, timeout: float = 10000) -> AutomationAPI:
        await self._page.wait_for_load_state("networkidle", timeout=timeout)
        return self

    async def screenshot(self, path: str = "screenshot.png", full_page: bool = True) -> str:
        return await self.screenshots.capture(path=path, full_page=full_page)

    async def get_title(self) -> str:
        return await self._page.title()

    async def get_url(self) -> str:
        return self._page.url

    async def run_js(self, script: str) -> Any:
        return await self._page.evaluate(script)

    async def inject_css(self, css: str) -> AutomationAPI:
        await self._page.add_style_tag(content=css)
        return self

    async def hover(self, selector: str) -> AutomationAPI:
        await self._page.hover(selector)
        return self

    async def scroll_to(self, selector: str) -> AutomationAPI:
        await self.page.scroll_to_element(selector)
        return self

    async def mock_api(self, url_pattern: str, response: Any) -> AutomationAPI:
        await self.network.start()
        self.network.mock_json(url_pattern, response)
        return self

    async def start_network_capture(self) -> AutomationAPI:
        await self.network.start()
        return self

    async def stop_network_capture(self) -> AutomationAPI:
        await self.network.stop()
        return self

    async def get_console_log(self) -> list[dict]:
        return [
            {"level": e.level, "text": e.text, "url": e.url}
            for e in self.monitor.get_console_log()
        ]
