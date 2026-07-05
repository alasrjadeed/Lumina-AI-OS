from typing import Any, Dict
from backend.app.services.ai.agents.base_agent import BaseAgent
from backend.app.services.crm.client_workspace import ClientWorkspace


class CustomerSuccessAgent(BaseAgent):
    def __init__(self, ai_engine, memory):
        super().__init__(
            name="Customer Success AI",
            role="Customer Success Manager",
            ai_engine=ai_engine,
            memory=memory,
        )
        self.workspace = ClientWorkspace(memory)

    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "onboard":
            ws = await self.workspace.create_workspace(params.get("company", ""), params.get("contact", {}))
            return {"status": "onboarded", "workspace": ws}
        elif action == "check_in":
            ws = await self.workspace.get_workspace(params.get("company", ""))
            if ws:
                tasks_pending = sum(1 for t in ws.get("tasks", []) if t.get("status") == "pending")
                return {"company": params.get("company", ""), "tasks_pending": tasks_pending, "status": "active"}
            return {"error": "Workspace not found"}
        elif action == "summary":
            return {"summary": await self.workspace.summary(params.get("company", ""))}
        thought = await self.think(f"Customer success: {action}")
        return {"status": "cs_action", "thought": thought}
