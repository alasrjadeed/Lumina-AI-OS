from __future__ import annotations

from enum import Enum
from typing import Any


class WaitStrategy(Enum):
    VISIBLE = "visible"
    HIDDEN = "hidden"
    ATTACHED = "attached"
    DETACHED = "detached"
    NETWORK_IDLE = "networkidle"
    LOAD = "load"
    DOM_CONTENT_LOADED = "domcontentloaded"
    CUSTOM = "custom"


class ScrollDirection(Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"


class PageInteractor:
    """Enhanced page interaction beyond basic navigation."""

    def __init__(self, page):
        self._page = page

    async def wait(
        self, strategy: WaitStrategy = WaitStrategy.VISIBLE,
        selector: str = "", timeout: float = 5000,
    ) -> bool:
        try:
            if strategy == WaitStrategy.VISIBLE and selector:
                await self._page.wait_for_selector(selector, state="visible", timeout=timeout)
            elif strategy == WaitStrategy.HIDDEN and selector:
                await self._page.wait_for_selector(selector, state="hidden", timeout=timeout)
            elif strategy == WaitStrategy.ATTACHED and selector:
                await self._page.wait_for_selector(selector, state="attached", timeout=timeout)
            elif strategy == WaitStrategy.DETACHED and selector:
                await self._page.wait_for_selector(selector, state="detached", timeout=timeout)
            elif strategy == WaitStrategy.NETWORK_IDLE:
                await self._page.wait_for_load_state("networkidle", timeout=timeout)
            elif strategy == WaitStrategy.LOAD:
                await self._page.wait_for_load_state("load", timeout=timeout)
            elif strategy == WaitStrategy.DOM_CONTENT_LOADED:
                await self._page.wait_for_load_state("domcontentloaded", timeout=timeout)
            else:
                await self._page.wait_for_timeout(timeout)
            return True
        except Exception:
            return False

    async def scroll(
        self, direction: ScrollDirection | str = ScrollDirection.DOWN,
        amount: int = 300,
    ) -> None:
        dir_map = {
            ScrollDirection.DOWN: (0, amount),
            ScrollDirection.UP: (0, -amount),
            ScrollDirection.LEFT: (-amount, 0),
            ScrollDirection.RIGHT: (amount, 0),
            ScrollDirection.TOP: (0, -999999),
            ScrollDirection.BOTTOM: (0, 999999),
        }
        if isinstance(direction, str):
            direction = ScrollDirection(direction)
        dx, dy = dir_map[direction]
        await self._page.evaluate(f"window.scrollBy({dx}, {dy})")

    async def scroll_to_element(self, selector: str) -> bool:
        try:
            js = (
                f"document.querySelector('{selector}')"
                "?.scrollIntoView({ behavior: 'smooth', block: 'center' })"
            )
            await self._page.evaluate(js)
            return True
        except Exception:
            return False

    async def hover(self, selector: str) -> None:
        await self._page.hover(selector)

    async def select_option(self, selector: str, value: str | list[str]) -> list[str]:
        return await self._page.select_option(selector, value)

    async def type_text(self, selector: str, text: str, delay: int = 0) -> None:
        await self._page.fill(selector, "")
        await self._page.type(selector, text, delay=delay)

    async def press_key(self, key: str) -> None:
        await self._page.keyboard.press(key)

    async def keyboard_type(self, text: str, delay: int = 0) -> None:
        await self._page.keyboard.type(text, delay=delay)

    async def switch_to_iframe(self, selector: str) -> Any | None:
        frame = await self._page.frame_locator(selector).owner_frame()
        return frame

    async def switch_to_tab(self, index: int) -> None:
        pages = self._page.context.pages
        if 0 <= index < len(pages):
            await pages[index].bring_to_front()

    async def open_new_tab(self, url: str = "") -> Any:
        page = await self._page.context.new_page()
        if url:
            await page.goto(url)
        return page

    async def close_current_tab(self) -> None:
        if len(self._page.context.pages) > 1:
            await self._page.close()

    async def get_tabs(self) -> list[dict]:
        return [
            {"url": p.url, "title": await p.title()}
            for p in self._page.context.pages
        ]

    async def inject_css(self, css: str) -> None:
        await self._page.add_style_tag(content=css)

    async def inject_js(self, script: str) -> Any:
        return await self._page.evaluate(script)

    async def pdf(self, path: str = "page.pdf", **kwargs: Any) -> None:
        await self._page.pdf(path=path, **kwargs)

    async def get_dimensions(self) -> dict[str, int]:
        return await self._page.evaluate("""() => ({
            viewport: { width: window.innerWidth, height: window.innerHeight },
            document: {
                width: document.documentElement.scrollWidth,
                height: document.documentElement.scrollHeight,
            },
        })""")
