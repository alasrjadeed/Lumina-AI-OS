"""Browser Agent — AI-controlled browser automation.

Instead of writing code, describe what you want and the agent does it.
Uses Playwright + AI provider chain for autonomous web tasks.
"""

from __future__ import annotations

import json
import re
from typing import Any

from core.browser.automation import browser
from core.log import log
from core.provider import engine


class BrowserAgent:
    """AI-powered browser agent that executes natural language tasks.

    Example:
        agent = BrowserAgent()
        result = await agent.execute("Go to google.com, search for 'Lumina AI', and take a screenshot")
    """

    def __init__(self):
        self._context: dict[str, Any] = {}

    async def execute(self, task: str, headless: bool = False) -> dict:
        """Execute a natural language browser task."""
        log.info("Browser Agent: Starting task: %s", task[:100])
        await browser.launch(headless=headless)

        plan = await self._plan(task)
        log.info("Browser Agent: Plan: %s", plan.get("summary", ""))

        results = []
        for step in plan.get("steps", []):
            try:
                result = await self._execute_step(step)
                results.append({"step": step, "status": "ok", "result": result})
            except Exception as e:
                log.error("Browser Agent: Step failed: %s - %s", step.get("action"), e)
                results.append({"step": step, "status": "error", "error": str(e)})
                if step.get("critical", False):
                    break

        await browser.close()
        return {"task": task, "plan": plan, "results": results}

    async def _plan(self, task: str) -> dict:
        """Use AI to create a step-by-step browser plan."""
        prompt = f"""You are a browser automation agent. Create a step-by-step plan for:

Task: {task}

Available actions:
- navigate(url) — Go to a URL
- click(selector) — Click an element  
- fill(selector, value) — Fill an input field
- select(selector, value) — Select an option
- screenshot(path) — Take a screenshot
- extract(selector) — Get text from an element
- extract_all(selector) — Get text from all matching elements
- wait(ms) — Wait for milliseconds
- scroll(direction) — Scroll up/down
- press_key(key) — Press a keyboard key (Enter, Tab, etc.)
- hover(selector) — Hover over an element

Return ONLY JSON:
{{
  "summary": "brief description of the plan",
  "steps": [
    {{"action": "navigate", "params": {{"url": "..."}}, "description": "what this step does"}},
    {{"action": "fill", "params": {{"selector": "#search", "value": "query"}}, "description": "..."}}
  ]
}}"""
        try:
            resp = await engine.chat([{"role": "user", "content": prompt}])
            text = resp.get("message", {}).get("content", "")
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            log.error("Browser Agent: Planning failed: %s", e)
        return {"summary": "Direct execution", "steps": [{"action": "navigate", "params": {"url": task}}]}

    async def _execute_step(self, step: dict) -> Any:
        """Execute a single plan step."""
        action = step.get("action", "")
        params = step.get("params", {})

        log.info("Browser Agent: %s - %s", action, params)

        if action == "navigate":
            url = params.get("url", "")
            if not url.startswith("http"):
                url = "https://" + url
            await browser.navigate(url)
            return {"title": await browser._page.title(), "url": url}

        if action == "click":
            selector = params.get("selector", "")
            await browser._page.wait_for_selector(selector, timeout=10000)
            await browser.click(selector)
            return {"clicked": selector}

        if action == "fill":
            selector = params.get("selector", "")
            value = params.get("value", "")
            await browser._page.wait_for_selector(selector, timeout=10000)
            await browser.fill(selector, value)
            return {"filled": selector, "value": value[:50]}

        if action == "select":
            await browser._page.select_option(params["selector"], params["value"])
            return {"selected": params["selector"]}

        if action == "screenshot":
            path = params.get("path", f"agent_{len(self._context)}.png")
            await browser.screenshot(path)
            return {"screenshot": path}

        if action == "extract":
            text = await browser.get_text(params["selector"])
            self._context["last_text"] = text
            return {"text": text[:500]}

        if action == "extract_all":
            els = await browser._page.query_selector_all(params["selector"])
            texts = [await el.inner_text() for el in els]
            return {"items": texts[:50]}

        if action == "wait":
            import asyncio
            await asyncio.sleep(params.get("ms", 1000) / 1000)
            return {"waited": params.get("ms", 1000)}

        if action == "scroll":
            await browser._page.evaluate(f"window.scrollBy(0, {params.get('amount', 500)})")
            return {"scrolled": True}

        if action == "press_key":
            await browser._page.keyboard.press(params["key"])
            return {"pressed": params["key"]}

        if action == "hover":
            await browser._page.hover(params["selector"])
            return {"hovered": params["selector"]}

        raise ValueError(f"Unknown action: {action}")


browser_agent = BrowserAgent()
