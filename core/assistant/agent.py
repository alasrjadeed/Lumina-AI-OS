"""AI Assistant Agent — understands tasks and executes them across all modules."""

from __future__ import annotations

import json
import re

from core.log import log
from core.provider import engine
from core.vault.store import vault

CAPABILITIES = {
    "browser": "Control Chrome browser — navigate, click, fill forms, take screenshots",
    "content": "Write blogs, emails, social posts, product descriptions, meta tags, "
    "quotes, invoices",
    "crm": "Manage contacts, deals, pipeline stages, sales analytics",
    "seo": "Analyze websites, generate meta tags, track keywords, site audits",
    "social": "Manage Facebook & Instagram pages, create posts, reply to comments, create ads",
    "whatsapp": "Send WhatsApp messages, manage product catalog, business messaging",
    "vault": "Store and retrieve personal & business information",
    "files": "Browse, read, create, and delete files on the local system",
    "android": "Control connected Android devices via ADB — tap, type, screenshot, install apps",
    "desktop": "Execute system commands, manage applications, clipboard operations",
    "vision": "Use the camera to see — capture images, detect objects, recognize faces, "
    "describe scenes",
}


class AssistantAgent:
    """AI assistant that understands natural language and executes tasks across all modules."""

    async def process(self, command: str) -> dict:
        """Process a natural language command and execute it."""
        log.info("Assistant: Processing: %s", command[:100])

        # First, understand the intent
        intent = await self._understand(command)

        if intent.get("error"):
            return {"command": command, "error": intent["error"]}

        action = intent.get("action", "")
        params = intent.get("params", {})

        # Route to the appropriate module
        if action == "content":
            return await self._handle_content(params, command)
        elif action == "browser":
            return await self._handle_browser(params, command)
        elif action == "crm":
            return await self._handle_crm(params)
        elif action == "seo":
            return await self._handle_seo(params)
        elif action == "social":
            return await self._handle_social(params)
        elif action == "whatsapp":
            return await self._handle_whatsapp(params)
        elif action == "vault":
            return await self._handle_vault(params)
        elif action == "android":
            return await self._handle_android(params)
        elif action == "vision":
            return await self._handle_vision(params)
        elif action == "files":
            return await self._handle_files(params)
        elif action == "chat":
            return await self._handle_chat(command)
        else:
            # Fallback to general AI chat
            return await self._handle_chat(command)

    async def _understand(self, command: str) -> dict:
        """Use AI to understand the intent and extract parameters."""
        caps_text = "\n".join([f"- {k}: {v}" for k, v in CAPABILITIES.items()])

        prompt = f"""You are a task router. Understand this command and return JSON:

Command: "{command}"

Available capabilities:
{caps_text}

Return ONLY JSON:
{{"action": "content|browser|crm|seo|social|whatsapp|vault|android|files|chat",
 "params": {{...relevant parameters...}},
 "summary": "brief description"}}

For content actions, params should include: type (blog|email|social_post|product_description|\
meta_title|meta_description|faq|landing_page|quote|invoice|whatsapp), topic, tone
For browser: task description
For CRM: sub_action (add_contact|add_deal|summary|list_contacts|list_deals)
For SEO: sub_action (audit|meta|keywords), url
For social: sub_action (create_post|add_page|reply), content, platform
For whatsapp: sub_action (send|add_product), to, text, name, price
For vault: sub_action (get|set), key, value
For android: sub_action (tap|type|screenshot|shell), command
For vision: sub_action (capture|detect|faces|describe)
For files: sub_action (list|read|write), path, content
For chat: just the conversation"""

        try:
            resp = await engine.chat([{"role": "user", "content": prompt}])
            text = resp.get("message", {}).get("content", "")
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            log.error("Assistant: Understanding failed: %s", e)

        return {"action": "chat", "params": {}, "summary": command}

    async def _handle_content(self, params: dict, command: str) -> dict:
        from core.writer.generator import writer

        ctype = params.get("type", "blog")
        topic = params.get("topic") or params.get("text") or command
        tone = params.get("tone", "professional")
        result = await writer.generate(ctype, topic, tone)
        return {"action": "content", "result": result.get("content", ""), "type": ctype}

    async def _handle_browser(self, params: dict, command: str) -> dict:
        from core.browser.agent import browser_agent

        task = params.get("task") or params.get("text") or command
        result = await browser_agent.execute(task, headless=False)
        return {"action": "browser", "result": result}

    async def _handle_crm(self, params: dict) -> dict:
        from core.crm.pipeline import crm

        sub = params.get("sub_action", "summary")
        if sub == "summary" or sub == "list":
            return {"action": "crm", "result": crm.get_sales_summary()}
        elif sub == "add_contact":
            return {
                "action": "crm",
                "result": crm.add_contact(params.get("name", ""), params.get("email", "")),
            }
        elif sub == "add_deal":
            return {
                "action": "crm",
                "result": crm.add_deal(params.get("title", ""), float(params.get("value", 0)), ""),
            }
        elif sub == "list_contacts":
            return {"action": "crm", "result": crm.list_contacts()}
        elif sub == "list_deals":
            return {"action": "crm", "result": crm.list_deals()}
        return {"action": "crm", "result": crm.get_sales_summary()}

    async def _handle_seo(self, params: dict) -> dict:
        from core.seo.analytics import seo

        sub = params.get("sub_action", "")
        if sub == "sites":
            return {"action": "seo", "result": seo.list_sites()}
        return {"action": "seo", "result": {"info": "SEO module ready"}}

    async def _handle_social(self, params: dict) -> dict:
        from core.social.manager import social

        sub = params.get("sub_action", "")
        if sub == "add_page":
            p = social.add_page(params.get("name", ""), params.get("platform", "facebook"))
            return {"action": "social", "result": f"Added page: {p.name}"}
        elif sub == "create_post":
            p = social.create_post(params.get("content", ""), params.get("platform", "facebook"))
            return {"action": "social", "result": f"Post created: {p.content[:50]}"}
        return {"action": "social", "result": social.get_stats()}

    async def _handle_whatsapp(self, params: dict) -> dict:
        from core.whatsapp.business import waba

        sub = params.get("sub_action", "")
        if sub == "add_product":
            p = waba.add_product(
                params.get("name", ""), params.get("description", ""), float(params.get("price", 0))
            )
            return {"action": "whatsapp", "result": f"Product added: {p.name} (${p.price})"}
        elif sub == "send":
            return {
                "action": "whatsapp",
                "result": f"Send message to {params.get('to', '')}: {params.get('text', '')}",
            }
        return {"action": "whatsapp", "result": waba.get_stats()}

    async def _handle_vault(self, params: dict) -> dict:
        sub = params.get("sub_action", "")
        if sub == "set":
            vault.set(params.get("key", ""), params.get("value", ""))
            return {"action": "vault", "result": f"Saved {params.get('key', '')}"}
        elif sub == "get":
            val = vault.get(params.get("key", ""))
            return {"action": "vault", "result": val or "Not found"}
        return {"action": "vault", "result": vault.all()}

    async def _handle_android(self, params: dict) -> dict:
        from core.android.device import android

        sub = params.get("sub_action", "")
        if sub == "screenshot" and android.is_connected:
            path = android.screenshot()
            return {"action": "android", "result": f"Screenshot saved: {path}"}
        elif sub == "type" and android.is_connected:
            android.input_text(params.get("text", ""))
            return {"action": "android", "result": "Text typed"}
        return {
            "action": "android",
            "result": "Android device: "
            + ("connected" if android.is_connected else "not connected"),
        }

    async def _handle_files(self, params: dict) -> dict:
        import os

        sub = params.get("sub_action", "list")
        path = params.get("path", ".")
        if sub == "list":
            items = os.listdir(path) if os.path.isdir(path) else []
            return {"action": "files", "result": items[:20]}
        return {"action": "files", "result": "File operations ready"}

    async def _handle_vision(self, params: dict) -> dict:
        from core.provider import engine as ai_engine
        from core.vision import CameraDevice, FaceDetector, ObjectDetector, SceneDescriber

        sub = params.get("sub_action", "capture")
        camera = CameraDevice(device_id=0)

        if sub == "capture":
            frame = await camera.capture_frame()
            if frame is None:
                return {"action": "vision", "result": "Failed to capture from camera."}
            return {
                "action": "vision",
                "result": f"Captured {frame.width}x{frame.height} image ({len(frame.data)} bytes).",
                "frame_info": frame.to_dict(),
            }
        elif sub == "detect":
            frame_np = await camera.capture_numpy()
            if frame_np is None:
                return {"action": "vision", "result": "Failed to capture frame for detection."}
            detector = ObjectDetector()
            await detector.initialize()
            result = await detector.detect(frame_np)
            await detector.close()
            return {"action": "vision", "result": result.summary(), "detections": result.to_dict()}
        elif sub == "faces":
            frame_np = await camera.capture_numpy()
            if frame_np is None:
                return {"action": "vision", "result": "Failed to capture frame for face detection."}
            detector = FaceDetector()
            result = await detector.detect(frame_np)
            return {"action": "vision", "result": result.summary(), "faces": result.to_dict()}
        elif sub == "describe":
            frame_np = await camera.capture_numpy()
            if frame_np is None:
                return {"action": "vision", "result": "Failed to capture frame for description."}
            describer = SceneDescriber(ai_engine=ai_engine)
            result = await describer.describe(frame_np)
            return {"action": "vision", "result": result.summary, "description": result.to_dict()}
        else:
            return {"action": "vision", "result": "Vision module ready."}

    async def _handle_chat(self, command: str) -> dict:
        resp = await engine.chat([{"role": "user", "content": command}])
        text = resp.get("message", {}).get("content", "")
        return {"action": "chat", "result": text}


assistant = AssistantAgent()
