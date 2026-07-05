from typing import Any, Dict, List
from backend.app.services.ai.agents.base_agent import BaseAgent
from backend.app.services.crm.quotation_generator import QuotationGenerator


class QuotationAgent(BaseAgent):
    def __init__(self, ai_engine, memory):
        super().__init__(
            name="Quotation AI",
            role="Quotation Specialist",
            ai_engine=ai_engine,
            memory=memory,
        )
        self.quotation_gen = QuotationGenerator(ai_engine)

    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "create":
            return await self.quotation_gen.create_quotation(
                params.get("client", ""),
                params.get("items", []),
                params.get("tax", 0.0),
                params.get("discount", 0.0),
            )
        thought = await self.think(f"Quotation: {action}")
        return {"status": "quotation_action", "thought": thought}
