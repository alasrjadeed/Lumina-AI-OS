import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from backend.app.services.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class FollowUpManager:
    def __init__(self, memory: MemoryManager):
        self.memory = memory
        self._namespace = "crm_followups"

    async def schedule(self, lead_id: str, days_from_now: int = 5, note: str = "") -> Dict[str, Any]:
        followup_date = datetime.now(timezone.utc) + timedelta(days=days_from_now)
        entry = {
            "lead_id": lead_id,
            "due_at": followup_date.isoformat(),
            "note": note,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        key = f"followup:{lead_id}:{followup_date.timestamp()}"
        await self.memory.store(key, entry, namespace=self._namespace)
        return entry

    async def get_pending(self) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        entries = await self.memory.list_namespace(self._namespace)
        pending = []
        for e in entries:
            val = e.get("value", {})
            if val.get("status") == "pending" and val.get("due_at", "") <= now:
                pending.append(val)
        return pending

    async def mark_done(self, followup_key: str) -> bool:
        entry = await self.memory.retrieve(followup_key, namespace=self._namespace)
        if entry:
            entry["status"] = "completed"
            await self.memory.store(followup_key, entry, namespace=self._namespace)
            return True
        return False

    async def prepare_draft(self, lead: Dict[str, Any], channel: str = "email") -> Dict[str, Any]:
        drafts = {
            "email": f"Subject: Following up\n\nDear {lead.get('company_name', 'there')},\n\nI wanted to follow up regarding our previous conversation...",
            "whatsapp": f"Hi! Just checking in regarding...",
            "sms": f"Hi, following up on our discussion.",
        }
        return {"channel": channel, "draft": drafts.get(channel, drafts["email"]), "lead": lead}
