from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TabInfo:
    id: int
    url: str = ""
    title: str = ""
    active: bool = False
    created: float = field(default_factory=time.time)


class TabManager:
    """Dedicated multi-tab and window management."""

    def __init__(self, page):
        self._page = page
        self._tab_counter = 0

    async def list_tabs(self) -> list[TabInfo]:
        pages = self._page.context.pages
        current = self._page
        result = []
        for i, p in enumerate(pages):
            result.append(TabInfo(
                id=i,
                url=p.url,
                title=await p.title(),
                active=p == current,
            ))
        return result

    async def switch_to(self, index: int) -> bool:
        pages = self._page.context.pages
        if 0 <= index < len(pages):
            await pages[index].bring_to_front()
            return True
        return False

    async def switch_to_url(self, url_pattern: str) -> bool:
        for p in self._page.context.pages:
            if url_pattern in p.url:
                await p.bring_to_front()
                return True
        return False

    async def open(self, url: str = "", background: bool = False) -> Any:
        page = await self._page.context.new_page()
        if url:
            if background:
                await page.goto(url)
            else:
                await page.goto(url)
                await page.bring_to_front()
        self._tab_counter += 1
        return page

    async def close(self, index: int = -1) -> bool:
        pages = self._page.context.pages
        if index == -1:
            idx = next((i for i, p in enumerate(pages) if p == self._page), -1)
            if idx < 0:
                return False
            index = idx
        if 0 <= index < len(pages):
            await pages[index].close()
            return True
        return False

    async def close_others(self, keep: int = -1) -> int:
        pages = self._page.context.pages
        if keep == -1:
            keep = next((i for i, p in enumerate(pages) if p == self._page), 0)
        closed = 0
        for i, p in enumerate(pages):
            if i != keep:
                await p.close()
                closed += 1
        return closed

    async def close_all(self) -> int:
        pages = list(self._page.context.pages)
        for p in pages:
            if p != self._page:
                await p.close()
        return len(pages) - 1

    async def duplicate(self) -> Any:
        page = await self._page.context.new_page()
        await page.goto(self._page.url)
        self._tab_counter += 1
        return page

    async def reopen(self) -> Any:
        page = await self._page.context.new_page()
        return page

    async def count(self) -> int:
        return len(self._page.context.pages)

    async def get_by_url(self, url_pattern: str) -> list[TabInfo]:
        return [
            t for t in await self.list_tabs()
            if url_pattern in t.url
        ]

    async def get_by_title(self, title_pattern: str) -> list[TabInfo]:
        return [
            t for t in await self.list_tabs()
            if title_pattern.lower() in t.title.lower()
        ]

    async def bring_to_front(self, index: int) -> bool:
        return await self.switch_to(index)
