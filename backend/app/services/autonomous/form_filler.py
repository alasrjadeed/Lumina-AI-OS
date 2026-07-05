import logging
import json
from typing import Any, Dict, List, Optional
from backend.app.services.ai.engine import AIEngine
from backend.app.services.browser.browser_service import BrowserService

logger = logging.getLogger(__name__)


class FormFillerService:
    def __init__(self, ai: AIEngine):
        self.ai = ai
        self.browser = BrowserService()
        self._initialized = False

    async def ensure_browser(self):
        if not self._initialized:
            await self.browser.initialize(headless=False)
            self._initialized = True

    async def fill_form(self, url: str, data: Dict[str, Any], submit: bool = True) -> Dict[str, Any]:
        await self.ensure_browser()
        nav_result = await self.browser.navigate(url)
        if "error" in nav_result:
            return {"error": f"Navigation failed: {nav_result['error']}"}

        page_content = await self.browser.get_content()
        html = page_content.get("html", "")

        system = "You are a form analyzer. Extract all form fields from the HTML. Return JSON array: [{\"label\":\"...\",\"type\":\"...\",\"name\":\"...\",\"id\":\"...\",\"placeholder\":\"...\",\"required\":true/false}]"
        fields_json = await self.ai.generate_json(prompt=f"Analyze this HTML form and extract all input fields:\n{html[:10000]}", system=system)
        fields = fields_json if isinstance(fields_json, list) else fields_json.get("fields", [])

        filled = []
        for field in fields:
            field_name = field.get("name", "") or field.get("id", "") or field.get("label", "")
            matched_value = self._match_field(field, data)
            if matched_value is not None:
                selector = field.get("name", "") or field.get("id", "")
                if selector:
                    try:
                        await self.browser.fill(selector, str(matched_value))
                        filled.append({"field": field_name, "value": str(matched_value)[:30], "status": "filled"})
                    except Exception as e:
                        filled.append({"field": field_name, "error": str(e), "status": "failed"})

        result = {"url": url, "fields_found": len(fields), "fields_filled": len(filled), "details": filled}
        if submit:
            try:
                submit_btn = await self._find_submit_button(html)
                if submit_btn:
                    await self.browser.click(submit_btn)
                    result["submitted"] = True
                else:
                    result["submitted"] = False
                    result["warning"] = "No submit button found"
            except Exception as e:
                result["submitted"] = False
                result["error"] = str(e)

        return result

    def _match_field(self, field: Dict, data: Dict) -> Any:
        label = (field.get("label", "") or field.get("placeholder", "") or "").lower()
        name = (field.get("name", "") or "").lower()
        field_id = (field.get("id", "") or "").lower()

        for key, value in data.items():
            key_lower = key.lower()
            if key_lower in label or key_lower in name or key_lower in field_id:
                return value
            if label and (key_lower in label or label in key_lower):
                return value

        field_type = field.get("type", "").lower()
        if field_type == "email" and "email" in data:
            return data["email"]
        if field_type in ("tel", "phone") and "phone" in data:
            return data["phone"]
        if field_type == "password" and "password" in data:
            return data["password"]

        return None

    async def _find_submit_button(self, html: str) -> Optional[str]:
        system = "Find the CSS selector for the submit button in this HTML. Return just the selector string."
        selector = await self.ai.generate(prompt=f"Find submit button selector in:\n{html[:5000]}", system=system)
        selector = selector.strip().strip("'\"`")
        return selector if selector else None

    async def create_social_account(self, platform: str, details: Dict[str, Any]) -> Dict[str, Any]:
        urls = {"facebook": "https://www.facebook.com/reg/", "instagram": "https://www.instagram.com/accounts/emailsignup/", "twitter": "https://twitter.com/i/flow/signup", "linkedin": "https://www.linkedin.com/signup"}
        url = urls.get(platform.lower())
        if not url:
            return {"error": f"Unsupported platform: {platform}. Supported: {list(urls.keys())}"}
        return await self.fill_form(url, details)

    async def close_browser(self):
        if self._initialized:
            await self.browser.close()
            self._initialized = False
