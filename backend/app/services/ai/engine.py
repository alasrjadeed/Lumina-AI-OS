import logging
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class AIProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"
    GEMINI = "gemini"


class AIEngine:
    def __init__(self, provider: AIProvider = AIProvider.OLLAMA):
        self._provider = provider
        self._client = None
        self._initialized = False

    async def initialize(self):
        try:
            if self._provider == AIProvider.OLLAMA:
                import ollama
                self._client = ollama
                await self._check_ollama()
            elif self._provider == AIProvider.OPENAI:
                from openai import AsyncOpenAI
                from backend.app.core.config import settings
                self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self._initialized = True
            logger.info(f"AI Engine initialized with provider: {self._provider}")
        except Exception as e:
            logger.warning(f"AI Engine init failed: {e}")

    async def _check_ollama(self):
        try:
            await self._client.list()
        except Exception:
            logger.warning("Ollama not running. Install: https://ollama.ai")

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        if not self._initialized:
            return "[AI Engine not initialized]"

        try:
            if self._provider == AIProvider.OLLAMA:
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})
                response = await self._client.chat(
                    model=model or "llama3",
                    messages=messages,
                    options={"temperature": temperature},
                )
                return response["message"]["content"]
            elif self._provider == AIProvider.OPENAI:
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})
                response = await self._client.chat.completions.create(
                    model=model or "gpt-4",
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return f"[Error: {e}]"

        return ""

    async def generate_json(
        self,
        prompt: str,
        system: Optional[str] = None,
    ) -> Dict[str, Any]:
        result = await self.generate(
            prompt=prompt,
            system=system or "Respond with valid JSON only.",
            temperature=0.1,
        )
        import json
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON", "raw": result}

    async def speech_to_text(self, audio_data: bytes) -> str:
        return "[transcript placeholder]"

    async def text_to_speech(self, text: str) -> bytes:
        return b""

    def switch_provider(self, provider: AIProvider):
        self._provider = provider
        self._initialized = False
        logger.info(f"Switched AI provider to: {provider}")
