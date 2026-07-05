import logging
from typing import Any, Dict, List, Optional
from backend.app.services.ai.engine import AIEngine
from backend.app.services.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class WhatsAppService:
    def __init__(self, ai: AIEngine, memory: MemoryManager):
        self.ai = ai
        self.memory = memory
        self._namespace = "whatsapp"
        self._api_key: Optional[str] = None
        self._phone_number_id: Optional[str] = None

    def configure(self, api_key: str, phone_number_id: str):
        self._api_key = api_key
        self._phone_number_id = phone_number_id
        logger.info("WhatsApp API configured")

    async def send_message(self, to: str, message: str, template: Optional[str] = None) -> Dict[str, Any]:
        if not self._api_key:
            return await self._simulate_send(to, message, template)
        try:
            import httpx
            url = f"https://graph.facebook.com/v18.0/{self._phone_number_id}/messages"
            headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "template" if template else "text",
                "text": {"body": message} if not template else {},
            }
            if template:
                payload["template"] = {"name": template, "language": {"code": "en"}}
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=headers)
                result = resp.json()
            await self._log_conversation(to, "sent", message, result)
            return {"to": to, "status": "sent", "provider": "cloud_api", "result": result}
        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}")
            return await self._simulate_send(to, message, template)

    async def _simulate_send(self, to: str, message: str, template: Optional[str] = None) -> Dict[str, Any]:
        await self._log_conversation(to, "sent", message, {"simulated": True})
        return {"to": to, "status": "sent (simulated)", "message": message[:50], "template": template}

    async def get_conversations(self, contact: Optional[str] = None) -> List[Dict[str, Any]]:
        entries = await self.memory.list_namespace(self._namespace)
        convs = [e.get("value", {}) for e in entries]
        if contact:
            convs = [c for c in convs if c.get("contact") == contact]
        return sorted(convs, key=lambda c: c.get("timestamp", ""), reverse=True)

    async def generate_reply(self, incoming_message: str, context: Optional[str] = None) -> str:
        system = "You are a professional WhatsApp business assistant. Reply helpfully and concisely."
        prompt = f"Customer message: {incoming_message}"
        if context:
            prompt += f"\nContext: {context}"
        return await self.ai.generate(prompt=prompt, system=system)

    async def schedule_message(self, to: str, message: str, schedule_at: str) -> Dict[str, Any]:
        entry = {"to": to, "message": message, "schedule_at": schedule_at, "status": "scheduled", "created_at": __import__("datetime").datetime.now().isoformat()}
        key = f"scheduled:{to}:{schedule_at}"
        await self.memory.store(key, entry, namespace=f"{self._namespace}_scheduled")
        return entry

    async def manage_catalog(self, action: str, product: Dict[str, Any]) -> Dict[str, Any]:
        key = f"product:{product.get('id', 'new')}"
        if action == "add":
            await self.memory.store(key, product, namespace=f"{self._namespace}_catalog")
            return {"status": "added", "product": product}
        elif action == "list":
            entries = await self.memory.list_namespace(f"{self._namespace}_catalog")
            return {"products": [e.get("value", {}) for e in entries]}
        elif action == "delete":
            await self.memory.delete(key, namespace=f"{self._namespace}_catalog")
            return {"status": "deleted"}
        return {"status": "unknown_action"}

    async def _log_conversation(self, contact: str, direction: str, message: str, metadata: dict):
        key = f"msg:{contact}:{__import__('time').time()}"
        entry = {"contact": contact, "direction": direction, "message": message, "metadata": metadata, "timestamp": __import__("datetime").datetime.now().isoformat()}
        await self.memory.store(key, entry, namespace=self._namespace)
