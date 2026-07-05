from typing import Any, Dict
from backend.app.services.ai.agents.base_agent import BaseAgent
from backend.app.services.desktop.desktop_service import DesktopService


class DesktopAgent(BaseAgent):
    def __init__(self, ai_engine, memory):
        super().__init__(
            name="Desktop Operator AI",
            role="OS Automation",
            ai_engine=ai_engine,
            memory=memory,
        )
        self.desktop = DesktopService()

    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "list_files":
            return await self.desktop.list_files(params.get("path", "."))
        elif action == "read_file":
            return await self.desktop.read_file(params.get("path", ""))
        elif action == "write_file":
            return await self.desktop.write_file(params.get("path", ""), params.get("content", ""))
        elif action == "screenshot":
            return await self.desktop.take_screenshot()
        elif action == "system_info":
            return await self.desktop.get_system_info()
        thought = await self.think(f"Desktop action: {action}")
        return {"status": "desktop_action", "thought": thought}
