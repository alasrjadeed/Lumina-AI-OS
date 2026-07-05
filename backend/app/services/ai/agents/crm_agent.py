from typing import Any, Dict
from backend.app.services.ai.agents.base_agent import BaseAgent
from backend.app.services.crm.client_workspace import ClientWorkspace
from backend.app.services.crm.followup_manager import FollowUpManager
from backend.app.services.crm.calendar_service import CalendarService


class CRMAgent(BaseAgent):
    def __init__(self, ai_engine, memory):
        super().__init__(
            name="CRM Manager AI",
            role="CRM Manager",
            ai_engine=ai_engine,
            memory=memory,
        )
        self.workspace = ClientWorkspace(memory)
        self.followups = FollowUpManager(memory)
        self.calendar = CalendarService(memory)

    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "workspace":
            ws = await self.workspace.get_workspace(params.get("company", ""))
            return ws or {"error": "Workspace not found"}
        elif action == "add_note":
            return await self.workspace.add_note(params.get("company", ""), params.get("note", ""))
        elif action == "add_task":
            return await self.workspace.add_task(params.get("company", ""), params.get("task", ""))
        elif action == "schedule_followup":
            return await self.followups.schedule(params.get("lead_id", ""), params.get("days", 5))
        elif action == "create_event":
            return await self.calendar.create_event(
                params.get("title", ""),
                params.get("start", ""),
                params.get("end", ""),
            )
        thought = await self.think(f"CRM action: {action}")
        return {"status": "crm_action", "thought": thought}
