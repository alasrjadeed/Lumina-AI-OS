import logging
from typing import Any, Dict, List, Optional
from backend.app.services.ai.engine import AIEngine

logger = logging.getLogger(__name__)


class VoiceNarratorService:
    def __init__(self, ai: AIEngine):
        self.ai = ai
        self._speaking = False
        self._paused = False
        self._speed = 1.0

    async def narrate(self, text: str, style: str = "neutral", speed: float = 1.0) -> Dict[str, Any]:
        self._speaking = True
        self._speed = speed
        system = f"Convert this text into a natural {style} narration. Add appropriate pauses and emphasis."
        narration = await self.ai.generate(prompt=f"Narrate: {text}", system=system)
        return {"text": narration, "style": style, "speed": speed, "status": "speaking", "displayed_content": text}

    async def pause(self) -> Dict[str, Any]:
        self._paused = True
        return {"status": "paused"}

    async def resume(self) -> Dict[str, Any]:
        self._paused = False
        return {"status": "resumed"}

    async def stop(self) -> Dict[str, Any]:
        self._speaking = False
        return {"status": "stopped"}

    async def set_speed(self, speed: float) -> Dict[str, Any]:
        self._speed = max(0.5, min(3.0, speed))
        return {"speed": self._speed}
