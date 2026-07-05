from typing import Any, Dict
from backend.app.services.ai.agents.base_agent import BaseAgent
from backend.app.services.marketing.designer_service import DesignerService


class DesignerAgent(BaseAgent):
    def __init__(self, ai_engine, memory):
        super().__init__(
            name="Designer AI",
            role="Creative Designer",
            ai_engine=ai_engine,
            memory=memory,
        )
        self.designer = DesignerService(ai_engine)

    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "logo":
            return await self.designer.generate_logo_description(
                params.get("brand", ""),
                params.get("industry", ""),
                params.get("style", "modern"),
            )
        elif action == "colors":
            return await self.designer.generate_brand_colors(params.get("brand", ""), params.get("industry", ""))
        elif action == "banner":
            return await self.designer.generate_banner(params.get("purpose", ""), params.get("dimensions", "1200x630"))
        thought = await self.think(f"Design: {action}")
        return {"status": "design_action", "thought": thought}
