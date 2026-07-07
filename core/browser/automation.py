try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None

from core.log import log


class BrowserAutomation:
    def __init__(self):
        self._playwright = None
        self._browser = None
        self._page = None

    async def _ensure_playwright(self):
        if self._playwright is None:
            if async_playwright is None:
                log.warning(
                    "Playwright not installed. Run: pip install playwright"
                    " && playwright install chromium",
                )
                raise ImportError("playwright is required")
            self._playwright = await async_playwright().start()
            log.info("Playwright started")

    async def launch(self, headless: bool = True):
        await self._ensure_playwright()
        self._browser = await self._playwright.chromium.launch(headless=headless)
        self._page = await self._browser.new_page()
        log.info("Browser launched (headless=%s)", headless)

    async def navigate(self, url: str):
        if not self._page:
            await self.launch()
        await self._page.goto(url, wait_until="networkidle")
        log.info("Navigated to %s", url)

    async def click(self, selector: str):
        await self._page.click(selector)

    async def fill(self, selector: str, value: str):
        await self._page.fill(selector, value)

    async def get_text(self, selector: str) -> str:
        return await self._page.inner_text(selector)

    async def get_html(self, selector: str | None = None) -> str:
        if selector:
            el = await self._page.query_selector(selector)
            return await el.inner_html() if el else ""
        return await self._page.content()

    async def screenshot(self, path: str = "screenshot.png"):
        await self._page.screenshot(path=path)
        return path

    async def extract_links(self) -> list[dict]:
        links = await self._page.eval_on_selector_all(
            "a[href]", "els => els.map(el => ({ text: el.innerText.trim(), href: el.href }))"
        )
        return [link for link in links if link["href"]]

    async def extract_forms(self) -> list[dict]:
        return await self._page.eval_on_selector_all(
            "form", """forms => forms.map(f => ({
                action: f.action,
                method: f.method,
                fields: Array.from(f.querySelectorAll('input, select, textarea')).map(el => ({
                    name: el.name,
                    type: el.type || el.tagName.toLowerCase(),
                    placeholder: el.placeholder || '',
                    required: el.required,
                    value: el.value
                }))
            }))"""
        )

    async def close(self):
        if self._browser:
            await self._browser.close()
            self._browser = None
            self._page = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        log.info("Browser closed")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()


browser = BrowserAutomation()
