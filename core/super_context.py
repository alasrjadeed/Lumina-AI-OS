"""SuperContext — pre-fetches relevant memory before the model reads user input."""

from __future__ import annotations

import time
from typing import Any

from core.memory.engine import MemoryEngine


class SuperContext:
    def __init__(self, memory: MemoryEngine | None = None):
        self._memory = memory
        self._cache: dict[str, tuple[str, float]] = {}
        self._cache_ttl = 30.0

    def set_memory(self, memory: MemoryEngine) -> None:
        self._memory = memory

    def _get_cached(self, key: str) -> str | None:
        entry = self._cache.get(key)
        if entry and (time.time() - entry[1]) < self._cache_ttl:
            return entry[0]
        return None

    def _set_cache(self, key: str, value: str) -> None:
        self._cache[key] = (value, time.time())
        if len(self._cache) > 100:
            cutoff = time.time() - self._cache_ttl
            self._cache = {k: v for k, v in self._cache.items() if v[1] > cutoff}

    def build_context(self, query: str, max_turns: int = 10) -> str:
        if not self._memory:
            return ""

        cache_key = f"{query}:{max_turns}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        parts: list[str] = []

        context = self._memory.recall_context_prompt(query, max_turns=max_turns)
        if context.strip():
            parts.append(context)

        facts = self._memory.semantic.query()
        if facts:
            fact_lines = [f"- {f.subject}: {f.object} (confidence: {f.confidence:.2f})" for f in facts[:10]]
            parts.append("## Known Facts\n" + "\n".join(fact_lines))

        episodes = self._memory.episodic.search(query, limit=3)
        if episodes:
            ep_lines = []
            for ep in episodes:
                ep_lines.append(f"- Task: {ep.task[:100]}")
                if ep.result:
                    ep_lines.append(f"  Result: {ep.result[:200]}")
            parts.append("## Related Episodes\n" + "\n".join(ep_lines))

        result = "\n\n".join(parts)
        self._set_cache(cache_key, result)
        return result

    def invalidate_cache(self, prefix: str = "") -> None:
        if prefix:
            self._cache = {k: v for k, v in self._cache.items() if not k.startswith(prefix)}
        else:
            self._cache.clear()


super_context = SuperContext()
