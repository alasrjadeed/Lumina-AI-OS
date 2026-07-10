from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from core.tools.base import ToolResult
from core.tools.registry import ToolRegistry


class ToolExecutor:
    """Executes tools with timeout, retry, caching, and parallel execution."""

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        default_timeout: float = 30.0,
        max_retries: int = 2,
        cache_ttl: float = 60.0,
    ):
        self.registry = registry or ToolRegistry()
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.cache_ttl = cache_ttl
        self._cache: dict[str, tuple[float, ToolResult]] = {}
        self._stats: dict[str, int] = {
            "executed": 0,
            "cached": 0,
            "failed": 0,
            "timed_out": 0,
        }

    async def execute(
        self,
        name: str,
        arguments: str | dict[str, Any] = "",
        timeout: float | None = None,
        retries: int | None = None,
    ) -> ToolResult:
        arg_str = arguments if isinstance(arguments, str) else str(sorted(arguments.items()))
        cache_key = f"{name}:{arg_str}"
        cached = self._check_cache(cache_key)
        if cached is not None:
            return cached

        tool = self.registry.get(name)
        if not tool:
            return ToolResult(success=False, error=f"Unknown tool: {name}")

        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}

        max_retries = retries if retries is not None else self.max_retries
        actual_timeout = timeout if timeout is not None else self.default_timeout

        for attempt in range(max_retries + 1):
            try:
                assert isinstance(arguments, dict)
                result = await asyncio.wait_for(
                    tool.execute(**{str(k): v for k, v in arguments.items()}),
                    timeout=actual_timeout,
                )
                if result.success:
                    self._cache[cache_key] = (time.time(), result)
                self._stats["executed"] += 1
                return result
            except TimeoutError:
                self._stats["timed_out"] += 1
                if attempt < max_retries:
                    continue
                return ToolResult(
                    success=False,
                    error=f"Tool {name} timed out after {actual_timeout}s",
                )
            except Exception as e:
                self._stats["failed"] += 1
                if attempt < max_retries:
                    continue
                return ToolResult(success=False, error=f"Tool {name} failed: {e}")

        return ToolResult(
            success=False,
            error=f"Tool {name} failed after {max_retries + 1} attempts",
        )

    async def execute_many(
        self,
        calls: list[tuple[str, str | dict[str, Any]]],
    ) -> list[ToolResult]:
        return await asyncio.gather(*(self.execute(name, args) for name, args in calls))

    def _check_cache(self, key: str) -> ToolResult | None:
        entry = self._cache.get(key)
        if entry is None:
            return None
        ts, result = entry
        if time.time() - ts > self.cache_ttl:
            del self._cache[key]
            return None
        self._stats["cached"] += 1
        return result

    def clear_cache(self) -> None:
        self._cache.clear()

    def stats(self) -> dict[str, int]:
        return dict(self._stats)

    def reset_stats(self) -> None:
        self._stats = {
            "executed": 0,
            "cached": 0,
            "failed": 0,
            "timed_out": 0,
        }
