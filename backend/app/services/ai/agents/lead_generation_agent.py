from typing import Any, Dict
from backend.app.services.ai.agents.base_agent import BaseAgent
from backend.app.services.crm.lead_generation import LeadGenerationService


class LeadGenerationAgent(BaseAgent):
    def __init__(self, ai_engine, memory):
        super().__init__(
            name="Lead Generation AI",
            role="Lead Generation Specialist",
            ai_engine=ai_engine,
            memory=memory,
        )
        self.lead_gen = LeadGenerationService(ai_engine, memory)

    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "search":
            return await self.lead_gen.search_businesses(
                params.get("criteria", ""),
                params.get("location", ""),
            )
        elif action == "enrich":
            return await self.lead_gen.enrich_lead(
                params.get("company_name", ""),
                params.get("website", ""),
            )
        elif action == "list":
            leads = await self.lead_gen.get_stored_leads()
            return {"leads": leads, "count": len(leads)}
        thought = await self.think(f"Lead generation: {action}")
        return {"status": "lead_gen_action", "thought": thought}
