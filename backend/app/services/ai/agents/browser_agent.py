from typing import Any, Dict
from backend.app.services.ai.agents.base_agent import BaseAgent
from backend.app.services.browser.browser_service import BrowserService


class BrowserAgent(BaseAgent):
    def __init__(self, ai_engine, memory):
        super().__init__(
            name="Browser Operator AI",
            role="Web Automation",
            ai_engine=ai_engine,
            memory=memory,
        )
        self.browser = BrowserService()

    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "navigate":
            return await self.browser.navigate(params.get("url", ""))
        elif action == "screenshot":
            return await self.browser.screenshot()
        elif action == "click":
            return await self.browser.click(params.get("selector", ""))
        elif action == "fill":
            return await self.browser.fill(params.get("selector", ""), params.get("value", ""))
        thought = await self.think(f"Browser action: {action}")
        return {"status": "browser_action", "thought": thought}
