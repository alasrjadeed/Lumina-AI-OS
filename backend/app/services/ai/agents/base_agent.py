import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from backend.app.services.ai.engine import AIEngine
from backend.app.services.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    def __init__(self, name: str, role: str, ai_engine: AIEngine, memory: MemoryManager):
        self.name = name
        self.role = role
        self.ai_engine = ai_engine
        self.memory = memory
        self._initialized = False

    @abstractmethod
    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        ...

    async def initialize(self):
        self._initialized = True
        logger.info(f"Agent '{self.name}' initialized")

    async def shutdown(self):
        self._initialized = False
        logger.info(f"Agent '{self.name}' shutdown")

    async def think(self, prompt: str, system: Optional[str] = None) -> str:
        return await self.ai_engine.generate(
            prompt=prompt,
            system=system or f"You are {self.name}, {self.role}. Respond helpfully.",
        )
