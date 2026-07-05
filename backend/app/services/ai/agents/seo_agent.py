from typing import Any, Dict
from backend.app.services.ai.agents.base_agent import BaseAgent
from backend.app.services.marketing.seo_service import SEOService


class SEOAgent(BaseAgent):
    def __init__(self, ai_engine, memory):
        super().__init__(
            name="SEO Specialist AI",
            role="SEO Specialist",
            ai_engine=ai_engine,
            memory=memory,
        )
        self.seo = SEOService(ai_engine)

    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "analyze":
            return await self.seo.analyze_page(params.get("url", ""), params.get("content", ""))
        elif action == "audit":
            return await self.seo.audit(params.get("url", ""))
        elif action == "keywords":
            return await self.seo.suggest_keywords(params.get("topic", ""))
        thought = await self.think(f"SEO action: {action}")
        return {"status": "seo_action", "thought": thought}
