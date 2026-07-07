
import httpx

from config.settings import settings


class WhatsAppClient:
    """WhatsApp Cloud API client (Meta) — free up to 1,000 conversations/month."""

    def __init__(self):
        self.api_key = settings.whatsapp_api_key or ""
        self.phone_number_id = settings.whatsapp_phone_id or ""
        self.base_url = "https://graph.facebook.com/v18.0"

    def _is_configured(self) -> bool:
        return bool(self.api_key and self.phone_number_id)

    async def _post(self, endpoint: str, data: dict) -> dict:
        if not self._is_configured():
            return {
                "error": "WhatsApp not configured. "
                "Set WHATSAPP_API_KEY and WHATSAPP_PHONE_ID in .env"
            }
        url = f"{self.base_url}/{self.phone_number_id}/{endpoint}"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=data, headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            })
            return resp.json()

    async def send_text(self, to: str, text: str) -> dict:
        return await self._post("messages", {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        })

    async def send_template(
        self, to: str, template_name: str, params: list[str] | None = None
    ) -> dict:
        components = []
        if params:
            components.append({
                "type": "body",
                "parameters": [{"type": "text", "text": p} for p in params],
            })
        return await self._post("messages", {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "en"},
                "components": components,
            },
        })

    async def send_image(self, to: str, image_url: str, caption: str = "") -> dict:
        return await self._post("messages", {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "image",
            "image": {"link": image_url, "caption": caption},
        })

    async def send_document(self, to: str, doc_url: str, filename: str = "") -> dict:
        return await self._post("messages", {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "document",
            "document": {"link": doc_url, "filename": filename},
        })

    async def mark_as_read(self, message_id: str) -> dict:
        return await self._post("messages", {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        })

    async def get_templates(self) -> list[dict]:
        if not self._is_configured():
            return []
        url = f"{self.base_url}/{self.phone_number_id}/message_templates"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers={"Authorization": f"Bearer {self.api_key}"})
            data = resp.json()
            return data.get("data", [])


whatsapp = WhatsAppClient()
