import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from backend.app.services.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class CalendarService:
    def __init__(self, memory: MemoryManager):
        self.memory = memory
        self._namespace = "crm_calendar"

    async def create_event(self, title: str, start: str, end: str, event_type: str = "meeting", description: str = "") -> Dict[str, Any]:
        event_id = f"event_{datetime.now(timezone.utc).timestamp()}"
        event = {
            "id": event_id,
            "title": title,
            "start": start,
            "end": end,
            "type": event_type,
            "description": description,
            "status": "scheduled",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await self.memory.store(event_id, event, namespace=self._namespace)
        return event

    async def list_events(self, date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[Dict]:
        entries = await self.memory.list_namespace(self._namespace)
        events = [e.get("value", {}) for e in entries]
        if date_from:
            events = [e for e in events if e.get("start", "") >= date_from]
        if date_to:
            events = [e for e in events if e.get("start", "") <= date_to]
        return sorted(events, key=lambda e: e.get("start", ""))

    async def delete_event(self, event_id: str) -> bool:
        return await self.memory.delete(event_id, namespace=self._namespace)
