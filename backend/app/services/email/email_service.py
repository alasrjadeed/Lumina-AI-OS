import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, List, Optional
from backend.app.services.ai.engine import AIEngine
from backend.app.services.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self, ai: AIEngine, memory: MemoryManager):
        self.ai = ai
        self.memory = memory
        self._namespace = "email"
        self._smtp_host: Optional[str] = None
        self._smtp_port: int = 587
        self._smtp_user: Optional[str] = None
        self._smtp_pass: Optional[str] = None

    def configure(self, smtp_host: str, smtp_port: int, smtp_user: str, smtp_pass: str):
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port
        self._smtp_user = smtp_user
        self._smtp_pass = smtp_pass
        logger.info(f"Email configured: {smtp_user} @ {smtp_host}")

    async def send_email(self, to: str, subject: str, body: str, html: Optional[str] = None) -> Dict[str, Any]:
        if not self._smtp_host:
            return await self._simulate_send(to, subject, body)
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self._smtp_user
            msg["To"] = to
            msg.attach(MIMEText(body, "plain"))
            if html:
                msg.attach(MIMEText(html, "html"))
            with smtplib.SMTP(self._smtp_host, self._smtp_port) as server:
                server.starttls()
                server.login(self._smtp_user, self._smtp_pass)
                server.sendmail(self._smtp_user, [to], msg.as_string())
            await self._log(to, "sent", {"subject": subject, "body_length": len(body)})
            return {"to": to, "subject": subject, "status": "sent", "provider": "smtp"}
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return await self._simulate_send(to, subject, body)

    async def _simulate_send(self, to: str, subject: str, body: str = "") -> Dict[str, Any]:
        await self._log(to, "sent (simulated)", {"subject": subject})
        return {"to": to, "subject": subject, "status": "sent (simulated)"}

    async def draft_email(self, prompt: str, tone: str = "professional") -> Dict[str, Any]:
        system = f"Write a {tone} email based on the prompt. Include subject line and body."
        content = await self.ai.generate(prompt=prompt, system=system)
        lines = content.split("\n", 1)
        subject = lines[0].replace("Subject:", "").replace("**", "").strip()
        body = lines[1] if len(lines) > 1 else content
        return {"subject": subject, "body": body, "tone": tone}

    async def track_reply(self, thread_id: str) -> Optional[Dict[str, Any]]:
        return await self.memory.retrieve(f"thread:{thread_id}", namespace=self._namespace)

    async def list_threads(self) -> List[Dict[str, Any]]:
        entries = await self.memory.list_namespace(self._namespace)
        return [e.get("value", {}) for e in entries if "thread" in e.get("key", "")]

    async def _log(self, to: str, status: str, metadata: dict):
        key = f"email:{to}:{__import__('time').time()}"
        await self.memory.store(key, {"to": to, "status": status, "metadata": metadata, "timestamp": __import__("datetime").datetime.now().isoformat()}, namespace=self._namespace)
