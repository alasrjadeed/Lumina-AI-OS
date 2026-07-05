import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BrowserService:
    def __init__(self):
        self._browser = None
        self._context = None
        self._page = None
        self._initialized = False

    async def initialize(self, headless: bool = True):
        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=headless)
            self._context = await self._browser.new_context()
            self._page = await self._context.new_page()
            self._initialized = True
            logger.info("Browser initialized")
        except ImportError:
            logger.warning("playwright not installed, browser unavailable")
        except Exception as e:
            logger.error(f"Browser init failed: {e}")

    async def navigate(self, url: str) -> Dict[str, Any]:
        if not self._initialized:
            return {"error": "Browser not initialized"}
        try:
            await self._page.goto(url, wait_until="networkidle")
            return {"url": self._page.url, "title": await self._page.title(), "status": "loaded"}
        except Exception as e:
            return {"error": str(e)}

    async def get_content(self) -> Dict[str, Any]:
        if not self._initialized:
            return {"error": "Browser not initialized"}
        try:
            content = await self._page.content()
            text = await self._page.evaluate("() => document.body.innerText")
            return {"html": content[:5000], "text": text[:5000], "url": self._page.url}
        except Exception as e:
            return {"error": str(e)}

    async def screenshot(self) -> Dict[str, Any]:
        if not self._initialized:
            return {"error": "Browser not initialized"}
        try:
            import base64
            screenshot = await self._page.screenshot(full_page=True)
            b64 = base64.b64encode(screenshot).decode()
            return {"image": b64, "format": "png", "size": len(b64)}
        except Exception as e:
            return {"error": str(e)}

    async def click(self, selector: str) -> Dict[str, Any]:
        if not self._initialized:
            return {"error": "Browser not initialized"}
        try:
            await self._page.click(selector)
            return {"selector": selector, "status": "clicked"}
        except Exception as e:
            return {"error": str(e)}

    async def fill(self, selector: str, value: str) -> Dict[str, Any]:
        if not self._initialized:
            return {"error": "Browser not initialized"}
        try:
            await self._page.fill(selector, value)
            return {"selector": selector, "status": "filled"}
        except Exception as e:
            return {"error": str(e)}

    async def evaluate(self, script: str) -> Dict[str, Any]:
        if not self._initialized:
            return {"error": "Browser not initialized"}
        try:
            result = await self._page.evaluate(script)
            return {"result": result}
        except Exception as e:
            return {"error": str(e)}

    async def close(self):
        if self._initialized:
            await self._browser.close()
            await self._playwright.stop()
            self._initialized = False
