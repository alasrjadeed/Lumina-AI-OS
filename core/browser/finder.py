from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ElementInfo:
    tag: str
    text: str = ""
    attributes: dict[str, str] = field(default_factory=dict)
    selector: str = ""
    visible: bool = False
    bounding_box: dict[str, float] | None = None


class ElementFinder:
    """Smart element discovery with multi-strategy fallback."""

    def __init__(self, page):
        self._page = page
        self._retry_delay = 100
        self._max_retries = 5

    async def find(self, text: str = "", selector: str = "", timeout: float = 5000) -> str | None:
        strategies = []
        if selector:
            strategies.append(("css", selector))
        if text:
            strategies.extend(
                [
                    ("text", text),
                    ("aria_label", text),
                    ("placeholder", text),
                    ("partial_text", text),
                    ("title_attr", text),
                    ("alt_text", text),
                ]
            )
        for name, value in strategies:
            result = await self._try_strategy(name, value, timeout)
            if result:
                return result
        return None

    async def find_all(self, selector: str) -> list[str]:
        try:
            els = await self._page.query_selector_all(selector)
            return [f"{selector}:nth-child({i})" for i in range(len(els))]
        except Exception:
            return []

    async def find_by_text(self, text: str, exact: bool = False) -> str | None:
        try:
            if exact:
                el = await self._page.query_selector(f'text="{text}"')
            else:
                el = await self._page.query_selector(f"text={text}")
            if el:
                return await self._get_unique_selector(el)
        except Exception:
            pass
        return None

    async def find_by_role(self, role: str, name: str = "") -> str | None:
        try:
            attr = f'[role="{role}"]'
            if name:
                attr += f'[aria-label*="{name}"]'
            el = await self._page.query_selector(attr)
            if el:
                return await self._get_unique_selector(el)
        except Exception:
            pass
        return None

    async def find_by_placeholder(self, text: str) -> str | None:
        try:
            el = await self._page.query_selector(f'[placeholder*="{text}"]')
            if el:
                return await self._get_unique_selector(el)
        except Exception:
            pass
        return None

    async def find_by_aria_label(self, label: str) -> str | None:
        try:
            el = await self._page.query_selector(f'[aria-label*="{label}"]')
            if el:
                return await self._get_unique_selector(el)
        except Exception:
            pass
        return None

    async def find_by_xpath(self, xpath: str) -> str | None:
        try:
            el = await self._page.query_selector(f"xpath={xpath}")
            if el:
                return await self._get_unique_selector(el)
        except Exception:
            pass
        return None

    async def find_near(self, text: str, near_selector: str, max_distance: int = 3) -> str | None:
        try:
            js = f"""
            (() => {{
                const ref = document.querySelector('{near_selector}');
                if (!ref) return null;
                const all = document.querySelectorAll('{text}');
                let best = null, bestDist = Infinity;
                for (const el of all) {{
                    const d = Math.abs(el.compareDocumentPosition(ref));
                    if (d < bestDist) {{ bestDist = d; best = el; }}
                }}
                return best ? best.tagName + (best.id ? '#' + best.id : '') : null;
            }})()
            """
            return await self._page.evaluate(js)
        except Exception:
            return None

    async def wait_for_element(self, selector: str, timeout: float = 10000) -> bool:
        try:
            await self._page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            return False

    async def get_element_info(self, selector: str) -> ElementInfo | None:
        try:
            info = await self._page.evaluate(f"""
            (() => {{
                const el = document.querySelector('{selector}');
                if (!el) return null;
                const box = el.getBoundingClientRect();
                const attrs = {{}};
                for (const a of el.attributes) {{ attrs[a.name] = a.value; }}
                return {{
                    tag: el.tagName.toLowerCase(),
                    text: (el.textContent || '').trim().slice(0, 200),
                    attributes: attrs,
                    visible: box.width > 0 && box.height > 0,
                    boundingBox: {{ x: box.x, y: box.y, width: box.width, height: box.height }},
                }};
            }})()
            """)
            if info:
                key_map = {"boundingBox": "bounding_box"}
                mapped = {str(key_map.get(k, k)): v for k, v in info.items()}
                return ElementInfo(**mapped)
        except Exception:
            pass
        return None

    async def is_visible(self, selector: str) -> bool:
        try:
            return await self._page.is_visible(selector)
        except Exception:
            return False

    async def is_enabled(self, selector: str) -> bool:
        try:
            return await self._page.is_enabled(selector)
        except Exception:
            return False

    async def _try_strategy(self, name: str, value: str, timeout: float) -> str | None:
        method_map = {
            "css": lambda: self._page.query_selector(value),
            "text": lambda: self._page.query_selector(f'text="{value}"'),
            "aria_label": lambda: self._page.query_selector(f'[aria-label="{value}"]'),
            "placeholder": lambda: self._page.query_selector(f'[placeholder*="{value}"]'),
            "partial_text": lambda: self._page.query_selector(f"text={value}"),
            "title_attr": lambda: self._page.query_selector(f'[title*="{value}"]'),
            "alt_text": lambda: self._page.query_selector(f'[alt*="{value}"]'),
        }
        fn = method_map.get(name)
        if not fn:
            return None
        try:
            el = await fn()
            if el:
                return await self._get_unique_selector(el)
        except Exception:
            pass
        return None

    async def _get_unique_selector(self, element) -> str:
        try:
            return await element.evaluate("""el => {
                if (el.id) return '#' + el.id;
                let path = el.tagName.toLowerCase();
                let parent = el.parentElement;
                while (parent && parent !== document.body) {
                    const idx = Array.from(parent.children).indexOf(el) + 1;
                    path = parent.tagName.toLowerCase() + ' > ' + path + ':nth-child(' + idx + ')';
                    el = parent;
                    parent = parent.parentElement;
                }
                return path;
            }""")
        except Exception:
            return ""
