from __future__ import annotations

import os
import sys
import time
from collections.abc import AsyncIterator
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.provider import engine
from jarvis.jarvis_settings import JarvisSettings


class CostTracker:
    def __init__(self):
        self.daily_counts: dict[str, int] = {}
        self.last_reset = time.time()

    def _ensure_reset(self):
        if time.time() - self.last_reset > 86400:
            self.daily_counts.clear()
            self.last_reset = time.time()

    def count(self, provider: str) -> int:
        self._ensure_reset()
        return self.daily_counts.get(provider, 0)

    def increment(self, provider: str) -> None:
        self._ensure_reset()
        self.daily_counts[provider] = self.daily_counts.get(provider, 0) + 1

    def can_use(self, provider: str) -> bool:
        usage = self.count(provider)
        limits = {
            "groq": 14400,
            "openrouter": 1000,
            "deepseek": 500,
            "openai": 500,
            "gemini": 1500,
        }
        return usage < limits.get(provider, 10000)


class SmartRouter:
    def __init__(self, settings: JarvisSettings):
        self.settings = settings
        self.cost = CostTracker()
        self._providers = engine._slots

    def _estimate_complexity(self, text: str) -> str:
        if len(text) < 50:
            return "simple"
        if any(
            w in text.lower()
            for w in ["code", "write", "create", "build", "debug", "analyze", "explain"]
        ):
            return "complex"
        if any(w in text.lower() for w in ["research", "compare", "evaluate", "summarize long"]):
            return "research"
        return "medium"

    async def chat(self, messages: list[dict], **kwargs) -> dict:
        text = messages[-1].get("content", "") if messages else ""
        complexity = self._estimate_complexity(text)
        offline = bool(self.settings.get("offline_mode", True))
        fallback = bool(self.settings.get("cloud_fallback", True))

        available = self._get_routed_providers(complexity, offline, fallback)
        errors = []
        for slot in available:
            if not self.cost.can_use(slot.provider.name):
                errors.append(f"{slot.provider.name}: daily limit")
                continue
            try:
                result = await slot.provider.chat(messages, **kwargs)
                self.cost.increment(slot.provider.name)
                return result
            except Exception as e:
                errors.append(f"{slot.provider.name}: {e}")
                continue
        raise Exception("All providers failed:\n" + "\n".join(errors))

    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        text = messages[-1].get("content", "") if messages else ""
        complexity = self._estimate_complexity(text)
        offline = bool(self.settings.get("offline_mode", True))
        fallback = bool(self.settings.get("cloud_fallback", True))

        available = self._get_routed_providers(complexity, offline, fallback)
        errors = []
        for slot in available:
            if not self.cost.can_use(slot.provider.name):
                errors.append(f"{slot.provider.name}: daily limit")
                continue
            try:
                stream = slot.provider.chat_stream(messages, **kwargs)
                async for token in stream:
                    yield token
                self.cost.increment(slot.provider.name)
                return
            except NotImplementedError:
                errors.append(f"{slot.provider.name}: no streaming")
                continue
            except Exception as e:
                errors.append(f"{slot.provider.name}: {e}")
                continue
        raise Exception("All providers failed for streaming:\n" + "\n".join(errors))

    def _get_routed_providers(self, complexity: str, offline: bool, fallback: bool) -> list[Any]:
        ordered = []
        for slot in self._providers:
            name = slot.provider.name
            if offline and name != "ollama" and not fallback:
                continue
            ordered.append(slot)

        def sort_key(slot):
            name = slot.provider.name
            priority = {
                "ollama": 0,
                "groq": 1,
                "openrouter": 2,
                "deepseek": 3,
                "openai": 4,
                "gemini": 5,
                "cloudflare": 6,
                "nvidia": 7,
            }
            return priority.get(name, 99)

        ordered.sort(key=sort_key)
        return ordered
