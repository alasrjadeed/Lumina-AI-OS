from typing import Any, Dict
from backend.app.services.ai.agents.base_agent import BaseAgent


class BusinessAgent(BaseAgent):
    def __init__(self, ai_engine, memory):
        super().__init__(
            name="Business AI",
            role="Business Manager",
            ai_engine=ai_engine,
            memory=memory,
        )

    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        result = await self.think(
            f"Handle business task: {action}\nParams: {params}",
            system="You are a business manager. Handle CRM, invoices, proposals efficiently.",
        )
        return {"status": "business_task_done", "result": result}
