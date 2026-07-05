from typing import Any, Dict
from backend.app.services.ai.agents.base_agent import BaseAgent
from backend.app.services.email.email_service import EmailService


class EmailAssistantAgent(BaseAgent):
    def __init__(self, ai_engine, memory):
        super().__init__(
            name="Email Assistant AI",
            role="Email Assistant",
            ai_engine=ai_engine,
            memory=memory,
        )
        self.email = EmailService(ai_engine, memory)

    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "send":
            return await self.email.send_email(
                params.get("to", ""),
                params.get("subject", ""),
                params.get("body", ""),
                params.get("html"),
            )
        elif action == "draft":
            return await self.email.draft_email(
                params.get("prompt", ""),
                params.get("tone", "professional"),
            )
        elif action == "track":
            return await self.email.track_reply(params.get("thread_id", ""))
        thought = await self.think(f"Email: {action}")
        return {"status": "email_action", "thought": thought}
