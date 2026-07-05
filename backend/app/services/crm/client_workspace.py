import logging
from typing import Any, Dict, List, Optional
from backend.app.services.memory.memory_manager import MemoryManager
from backend.app.services.crm.lead_manager import LeadManager
from backend.app.services.crm.followup_manager import FollowUpManager
from backend.app.services.crm.calendar_service import CalendarService

logger = logging.getLogger(__name__)


class ClientWorkspace:
    def __init__(self, memory: MemoryManager):
        self.memory = memory
        self._namespace = "crm_workspaces"
        self.lead_manager = LeadManager(memory)
        self.followups = FollowUpManager(memory)
        self.calendar = CalendarService(memory)

    async def create_workspace(self, company: str, contact: Dict[str, Any]) -> Dict[str, Any]:
        ws = {
            "company": company,
            "contact": contact,
            "meetings": [],
            "emails": [],
            "proposals": [],
            "quotations": [],
            "projects": [],
            "tasks": [],
            "invoices": [],
            "documents": [],
            "notes": [],
            "support_tickets": [],
            "followup_timeline": [],
            "created_at": __import__("datetime").datetime.now().isoformat(),
        }
        await self.memory.store(f"workspace:{company}", ws, namespace=self._namespace)
        return ws

    async def get_workspace(self, company: str) -> Optional[Dict[str, Any]]:
        return await self.memory.retrieve(f"workspace:{company}", namespace=self._namespace)

    async def add_note(self, company: str, note: str) -> Optional[Dict[str, Any]]:
        ws = await self.get_workspace(company)
        if ws:
            ws["notes"].append({"text": note, "at": __import__("datetime").datetime.now().isoformat()})
            await self.memory.store(f"workspace:{company}", ws, namespace=self._namespace)
        return ws

    async def add_task(self, company: str, task: str) -> Optional[Dict[str, Any]]:
        ws = await self.get_workspace(company)
        if ws:
            ws["tasks"].append({"text": task, "status": "pending", "at": __import__("datetime").datetime.now().isoformat()})
            await self.memory.store(f"workspace:{company}", ws, namespace=self._namespace)
        return ws

    async def summary(self, company: str) -> str:
        ws = await self.get_workspace(company)
        if not ws:
            return f"No workspace found for {company}"
        return f"""# {company} Workspace
Contact: {ws.get('contact', {})}
Proposals: {len(ws['proposals'])}
Projects: {len(ws['projects'])}
Open Tasks: {sum(1 for t in ws['tasks'] if t.get('status') == 'pending')}
Pending Invoices: {len(ws['invoices'])}
Support Tickets: {len(ws['support_tickets'])}
Recent Notes: {len(ws['notes'])}"""
