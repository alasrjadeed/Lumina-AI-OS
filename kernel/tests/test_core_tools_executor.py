from __future__ import annotations

import asyncio

import pytest

from core.tools.base import Tool, ToolResult
from core.tools.executor import ToolExecutor
from core.tools.registry import ToolRegistry


class FastTool(Tool):
    name = "fast"
    description = "Returns immediately"
    parameters = {"type": "object", "properties": {}}

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, output="fast done")


class SlowTool(Tool):
    name = "slow"
    description = "Takes time"
    parameters = {"type": "object", "properties": {}}

    async def execute(self, **kwargs) -> ToolResult:
        await asyncio.sleep(5)
        return ToolResult(success=True, output="slow done")


class FlakyTool(Tool):
    name = "flaky"
    description = "Fails first time"
    parameters = {"type": "object", "properties": {}}
    attempts = 0

    async def execute(self, **kwargs) -> ToolResult:
        self.attempts += 1
        if self.attempts < 2:
            raise RuntimeError("transient error")
        return ToolResult(success=True, output="flaky done")


class TestToolExecutor:
    @pytest.mark.asyncio
    async def test_execute_success(self):
        reg = ToolRegistry()
        reg.register(FastTool())
        ex = ToolExecutor(registry=reg)
        result = await ex.execute("fast")
        assert result.success
        assert result.output == "fast done"

    @pytest.mark.asyncio
    async def test_execute_unknown(self):
        ex = ToolExecutor()
        result = await ex.execute("unknown")
        assert not result.success
        assert "Unknown tool" in result.error

    @pytest.mark.asyncio
    async def test_execute_times_out(self):
        reg = ToolRegistry()
        reg.register(SlowTool())
        ex = ToolExecutor(registry=reg, default_timeout=0.5)
        result = await ex.execute("slow")
        assert not result.success
        assert "timed out" in result.error

    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        reg = ToolRegistry()
        tool = FlakyTool()
        reg.register(tool)
        ex = ToolExecutor(registry=reg, max_retries=2)
        result = await ex.execute("flaky")
        assert result.success
        assert result.output == "flaky done"

    @pytest.mark.asyncio
    async def test_cache_hit(self):
        reg = ToolRegistry()
        reg.register(FastTool())
        ex = ToolExecutor(registry=reg, cache_ttl=60)
        await ex.execute("fast")
        await ex.execute("fast")
        assert ex.stats()["cached"] >= 1

    @pytest.mark.asyncio
    async def test_clear_cache(self):
        reg = ToolRegistry()
        reg.register(FastTool())
        ex = ToolExecutor(registry=reg, cache_ttl=60)
        await ex.execute("fast")
        ex.clear_cache()
        await ex.execute("fast")
        assert ex.stats()["cached"] == 0

    @pytest.mark.asyncio
    async def test_execute_many(self):
        reg = ToolRegistry()
        reg.register(FastTool())
        ex = ToolExecutor(registry=reg)
        results = await ex.execute_many([("fast", {}), ("fast", {})])
        assert len(results) == 2
        assert all(r.success for r in results)

    def test_stats(self):
        ex = ToolExecutor()
        stats = ex.stats()
        assert "executed" in stats
        assert "cached" in stats
        assert "failed" in stats
        assert "timed_out" in stats

    def test_reset_stats(self):
        ex = ToolExecutor()
        ex._stats["executed"] = 10
        ex.reset_stats()
        assert ex.stats()["executed"] == 0
