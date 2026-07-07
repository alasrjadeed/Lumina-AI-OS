from __future__ import annotations

import json


class DOMInteraction:
    """Advanced DOM manipulation and querying."""

    def __init__(self, page):
        self._page = page

    async def query_all(self, selector: str, properties: list[str] | None = None) -> list[dict]:
        props = properties or ["tagName", "id", "className", "textContent"]
        props_js = ", ".join(f"{p}: el.{p}" for p in props)
        return await self._page.evaluate(f"""
            Array.from(document.querySelectorAll('{selector}')).map(el => ({{ {props_js} }}))
        """)

    async def get_computed_style(self, selector: str, property: str = "") -> list[dict] | str:
        if property:
            return await self._page.evaluate(f"""
                getComputedStyle(document.querySelector('{selector}')).getPropertyValue('{property}')
            """)
        return await self._page.evaluate(f"""
            (() => {{
                const el = document.querySelector('{selector}');
                if (!el) return [];
                const s = getComputedStyle(el);
                const props = ['color', 'background-color', 'font-size', 'font-family',
                    'display', 'visibility', 'opacity', 'position', 'z-index',
                    'width', 'height', 'margin', 'padding', 'border'];
                return props.map(p => ({{ property: p, value: s.getPropertyValue(p) }}));
            }})()
        """)

    async def set_attribute(self, selector: str, attr: str, value: str) -> None:
        await self._page.evaluate(f"""
            document.querySelector('{selector}')?.setAttribute('{attr}', '{value}')
        """)

    async def remove_attribute(self, selector: str, attr: str) -> None:
        await self._page.evaluate(f"""
            document.querySelector('{selector}')?.removeAttribute('{attr}')
        """)

    async def add_class(self, selector: str, class_name: str) -> None:
        await self._page.evaluate(f"""
            document.querySelector('{selector}')?.classList.add('{class_name}')
        """)

    async def remove_class(self, selector: str, class_name: str) -> None:
        await self._page.evaluate(f"""
            document.querySelector('{selector}')?.classList.remove('{class_name}')
        """)

    async def toggle_class(self, selector: str, class_name: str) -> None:
        await self._page.evaluate(f"""
            document.querySelector('{selector}')?.classList.toggle('{class_name}')
        """)

    async def set_html(self, selector: str, html: str) -> None:
        escaped = html.replace("`", "\\`").replace("${", "\\${")
        await self._page.evaluate(f"""
            document.querySelector('{selector}').innerHTML = `{escaped}`
        """)

    async def set_text(self, selector: str, text: str) -> None:
        await self._page.evaluate(f"""
            document.querySelector('{selector}').textContent = `{text}`
        """)

    async def remove_element(self, selector: str) -> None:
        await self._page.evaluate(f"""
            document.querySelector('{selector}')?.remove()
        """)

    async def insert_html(self, selector: str, html: str, position: str = "beforeend") -> None:
        await self._page.evaluate(f"""
            document.querySelector('{selector}')?.insertAdjacentHTML('{position}', `{html}`)
        """)

    async def find_by_computed_style(self, property: str, value: str, tag: str = "*") -> list[str]:
        return await self._page.evaluate(f"""
            Array.from(document.querySelectorAll('{tag}'))
                .filter(el => getComputedStyle(el).getPropertyValue('{property}') === '{value}')
                .map(el => el.tagName + (el.id ? '#' + el.id : ''))
        """)

    async def get_attributes(self, selector: str) -> dict[str, str]:
        return await self._page.evaluate(f"""
            (() => {{
                const el = document.querySelector('{selector}');
                if (!el) return {{}};
                const attrs = {{}};
                for (const a of el.attributes) {{ attrs[a.name] = a.value; }}
                return attrs;
            }})()
        """)

    async def focus(self, selector: str) -> None:
        await self._page.evaluate(f"document.querySelector('{selector}')?.focus()")

    async def blur(self, selector: str) -> None:
        await self._page.evaluate(f"document.querySelector('{selector}')?.blur()")

    async def dispatch_event(self, selector: str, event: str, detail: dict | None = None) -> None:
        detail_js = json.dumps(detail) if detail else "{}"
        await self._page.evaluate(f"""
            const el = document.querySelector('{selector}');
            if (el) el.dispatchEvent(new CustomEvent('{event}', {{ detail: {detail_js} }}));
        """)

    async def get_text_content(self, selector: str) -> str:
        return await self._page.evaluate(f"""
            document.querySelector('{selector}')?.textContent?.trim() || ''
        """)

    async def get_value(self, selector: str) -> str:
        return await self._page.evaluate(f"""
            document.querySelector('{selector}')?.value || ''
        """)

    async def set_value(self, selector: str, value: str) -> None:
        await self._page.evaluate(f"""
            const el = document.querySelector('{selector}');
            if (el) {{
                el.value = '{value}';
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
        """)

    async def get_dimensions(self, selector: str) -> dict[str, float]:
        return await self._page.evaluate(f"""
            (() => {{
                const el = document.querySelector('{selector}');
                if (!el) return null;
                const r = el.getBoundingClientRect();
                return {{ x: r.x, y: r.y, width: r.width, height: r.height,
                    top: r.top, right: r.right, bottom: r.bottom, left: r.left }};
            }})()
        """)

    async def is_visible(self, selector: str) -> bool:
        return await self._page.evaluate(f"""
            (() => {{
                const el = document.querySelector('{selector}');
                if (!el) return false;
                const s = getComputedStyle(el);
                return s.display !== 'none' && s.visibility !== 'hidden' && s.opacity !== '0';
            }})()
        """)

    async def scroll_into_view(self, selector: str, block: str = "center") -> None:
        await self._page.evaluate(f"""
            document.querySelector('{selector}')?.scrollIntoView({{ block: '{block}' }})
        """)

    async def wait_for_element(self, selector: str, timeout: float = 5000) -> bool:
        try:
            await self._page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            return False

    async def get_children(self, selector: str) -> list[dict]:
        return await self._page.evaluate(f"""
            Array.from(document.querySelector('{selector}')?.children || []).map(el => ({{
                tag: el.tagName.toLowerCase(),
                id: el.id,
                classes: el.className,
                text: (el.textContent || '').trim().slice(0, 100),
                childCount: el.children.length,
            }}))
        """)

    async def get_parent(self, selector: str) -> dict | None:
        return await self._page.evaluate(f"""
            (() => {{
                const el = document.querySelector('{selector}');
                if (!el || !el.parentElement) return null;
                const p = el.parentElement;
                return {{ tag: p.tagName.toLowerCase(), id: p.id, classes: p.className }};
            }})()
        """)
