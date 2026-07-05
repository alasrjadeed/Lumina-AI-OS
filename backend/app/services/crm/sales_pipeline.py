import logging
from typing import Any, Dict, List, Optional
from backend.app.services.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

STAGES = ["new", "qualified", "meeting_scheduled", "proposal_sent", "negotiation", "won", "onboarding", "support"]


class SalesPipeline:
    def __init__(self, memory: MemoryManager):
        self.memory = memory
        self._namespace = "crm_pipeline"

    async def move_stage(self, lead_id: str, to_stage: str) -> Optional[Dict[str, Any]]:
        if to_stage not in STAGES:
            return {"error": f"Invalid stage: {to_stage}. Valid: {STAGES}"}
        from backend.app.services.crm.lead_manager import LeadManager
        lm = LeadManager(self.memory)
        lead = await lm.get_lead(lead_id)
        if not lead:
            return {"error": "Lead not found"}
        lead["status"] = to_stage
        lead["stage_changed_at"] = __import__("datetime").datetime.now().isoformat()
        await lm.update_lead(lead_id, lead)
        await self.memory.store(f"pipeline:{lead_id}", {"lead_id": lead_id, "stage": to_stage}, namespace=self._namespace)
        return lead

    async def get_pipeline(self) -> Dict[str, List]:
        result = {stage: [] for stage in STAGES}
        entries = await self.memory.list_namespace(self._namespace)
        from backend.app.services.crm.lead_manager import LeadManager
        lm = LeadManager(self.memory)
        for entry in entries:
            val = entry.get("value", {})
            lead = await lm.get_lead(val.get("lead_id", ""))
            if lead:
                stage = lead.get("status", "new")
                if stage in result:
                    result[stage].append(lead)
        return result
