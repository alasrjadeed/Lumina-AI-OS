import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from backend.app.services.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class LeadManager:
    def __init__(self, memory: MemoryManager):
        self.memory = memory
        self._namespace = "crm_leads"

    async def create_lead(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        lead_id = f"lead_{datetime.now(timezone.utc).timestamp()}"
        lead["id"] = lead_id
        lead["status"] = "new"
        lead["score"] = 0
        lead["created_at"] = datetime.now(timezone.utc).isoformat()
        lead["last_contact"] = None
        lead["next_followup"] = None
        await self.memory.store(lead_id, lead, namespace=self._namespace)
        logger.info(f"Lead created: {lead.get('company_name', lead_id)}")
        return lead

    async def get_lead(self, lead_id: str) -> Optional[Dict[str, Any]]:
        return await self.memory.retrieve(lead_id, namespace=self._namespace)

    async def update_lead(self, lead_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        lead = await self.get_lead(lead_id)
        if not lead:
            return None
        lead.update(updates)
        await self.memory.store(lead_id, lead, namespace=self._namespace)
        return lead

    async def delete_lead(self, lead_id: str) -> bool:
        return await self.memory.delete(lead_id, namespace=self._namespace)

    async def list_leads(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        leads = await self.memory.list_namespace(self._namespace)
        if status:
            return [l for l in leads if l.get("value", {}).get("status") == status]
        return [l.get("value", {}) for l in leads]

    async def qualify_lead(self, lead_id: str) -> Dict[str, Any]:
        lead = await self.get_lead(lead_id)
        if not lead:
            return {"error": "Lead not found"}
        score = 0
        if lead.get("email"): score += 20
        if lead.get("phone"): score += 15
        if lead.get("website"): score += 10
        if lead.get("industry"): score += 10
        lead["score"] = score
        lead["status"] = "qualified" if score >= 30 else "contact"
        await self.memory.store(lead_id, lead, namespace=self._namespace)
        return lead
