from typing import Any, Dict
from backend.app.services.ai.agents.base_agent import BaseAgent
from backend.app.services.voice.narrator_service import VoiceNarratorService


class VoiceNarratorAgent(BaseAgent):
    def __init__(self, ai_engine, memory):
        super().__init__(
            name="Voice Narrator AI",
            role="Voice Narrator",
            ai_engine=ai_engine,
            memory=memory,
        )
        self.narrator = VoiceNarratorService(ai_engine)

    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "narrate":
            return await self.narrator.narrate(
                params.get("text", ""),
                params.get("style", "neutral"),
                params.get("speed", 1.0),
            )
        elif action == "pause":
            return await self.narrator.pause()
        elif action == "resume":
            return await self.narrator.resume()
        elif action == "stop":
            return await self.narrator.stop()
        thought = await self.think(f"Narration: {action}")
        return {"status": "narrator_action", "thought": thought}
