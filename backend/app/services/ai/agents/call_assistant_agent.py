from typing import Any, Dict
from backend.app.services.ai.agents.base_agent import BaseAgent
from backend.app.services.memory.memory_manager import MemoryManager


class CallAssistantAgent(BaseAgent):
    def __init__(self, ai_engine, memory):
        super().__init__(
            name="Call Assistant AI",
            role="Call Assistant",
            ai_engine=ai_engine,
            memory=memory,
        )
        self._namespace = "calls"

    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "prepare":
            talking_points = await self.think(
                f"Prepare talking points for a call with {params.get('contact', 'client')} about {params.get('topic', '')}",
                system="Generate concise talking points for a business call.",
            )
            return {"contact": params.get("contact", ""), "talking_points": talking_points, "status": "prepared"}
        elif action == "summarize":
            summary = await self.think(
                f"Summarize this call conversation:\n{params.get('transcript', '')}",
                system="Provide a concise call summary with action items.",
            )
            return {"summary": summary}
        elif action == "schedule":
            return {"contact": params.get("contact", ""), "scheduled_at": params.get("time", ""), "status": "scheduled"}
        thought = await self.think(f"Call: {action}")
        return {"status": "call_action", "thought": thought}
