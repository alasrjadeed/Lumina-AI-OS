from typing import Any, Dict
from backend.app.services.ai.agents.base_agent import BaseAgent
from backend.app.services.crm.lead_manager import LeadManager
from backend.app.services.crm.proposal_generator import ProposalGenerator


class SalesAgent(BaseAgent):
    def __init__(self, ai_engine, memory):
        super().__init__(
            name="Sales Manager AI",
            role="Sales Manager",
            ai_engine=ai_engine,
            memory=memory,
        )
        self.lead_manager = LeadManager(memory)
        self.proposal_gen = ProposalGenerator(ai_engine)

    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "create_lead":
            return await self.lead_manager.create_lead(params.get("lead", {}))
        elif action == "qualify_lead":
            return await self.lead_manager.qualify_lead(params.get("lead_id", ""))
        elif action == "generate_proposal":
            return await self.proposal_gen.generate(
                params.get("client", ""),
                params.get("scope", ""),
                params.get("pricing", ""),
                params.get("timeline", ""),
            )
        thought = await self.think(f"Handle sales action: {action} with {params}")
        return {"status": "sales_action", "thought": thought}
