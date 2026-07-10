from __future__ import annotations

import pytest

from core.agents.base import BaseAgent
from core.agents.manager import AgentManager, AgentMetadata


class TestAgentManager:
    def test_register_and_list(self):
        mgr = AgentManager()
        mgr.register(BaseAgent(name="TestBot"))
        assert "TestBot" in mgr.list()

    def test_register_duplicate_raises(self):
        mgr = AgentManager()
        mgr.register(BaseAgent(name="Bot"))
        with pytest.raises(ValueError, match="already registered"):
            mgr.register(BaseAgent(name="Bot"))

    def test_get(self):
        mgr = AgentManager()
        agent = BaseAgent(name="MyBot")
        mgr.register(agent)
        assert mgr.get("MyBot") is agent
        assert mgr.get("Nonexistent") is None

    def test_unregister(self):
        mgr = AgentManager()
        mgr.register(BaseAgent(name="Bot"))
        mgr.unregister("Bot")
        assert mgr.get("Bot") is None

    def test_register_with_metadata(self):
        mgr = AgentManager()
        meta = AgentMetadata(name="Bot", capabilities=["code", "debug"], model="gpt-4")
        mgr.register(BaseAgent(name="Bot"), metadata=meta)
        retrieved = mgr.get_metadata("Bot")
        assert retrieved is not None
        assert "code" in retrieved.capabilities
        assert retrieved.model == "gpt-4"

    def test_list_with_metadata(self):
        mgr = AgentManager()
        mgr.register(BaseAgent(name="A"), AgentMetadata(name="A"))
        mgr.register(BaseAgent(name="B"), AgentMetadata(name="B"))
        items = mgr.list_with_metadata()
        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_run_unknown_agent(self):
        mgr = AgentManager()
        result = await mgr.run("nonexistent", "do something")
        assert result.status == "error"
        assert "Unknown agent" in (result.error or "")

    @pytest.mark.asyncio
    async def test_run_agent_tracks_stats(self):
        mgr = AgentManager()
        meta = AgentMetadata(name="Bot")
        mgr.register(BaseAgent(name="Bot"), metadata=meta)
        await mgr.run("Bot", "say hello")
        meta = mgr.get_metadata("Bot")
        assert meta is not None
        assert meta.task_count == 1

    def test_health_all_healthy(self):
        mgr = AgentManager()
        mgr.register(BaseAgent(name="A"), AgentMetadata(name="A"))
        mgr.register(BaseAgent(name="B"), AgentMetadata(name="B"))
        health = mgr.health()
        assert all(v == "healthy" for v in health.values())

    def test_health_unhealthy(self):
        mgr = AgentManager()
        meta = AgentMetadata(name="Bad")
        meta.error_count = 11
        meta.task_count = 10
        mgr.register(BaseAgent(name="Bad"), metadata=meta)
        health = mgr.health()
        assert health["Bad"] == "unhealthy"

    def test_register_many(self):
        mgr = AgentManager()
        mgr.register_many({"A": BaseAgent(name="A"), "B": BaseAgent(name="B")})
        assert len(mgr.list()) == 2

    def test_route_picks_best_agent(self):
        mgr = AgentManager()
        mgr.register(
            BaseAgent(name="CodeBot"),
            AgentMetadata(name="CodeBot", capabilities=["code", "python"]),
        )
        mgr.register(
            BaseAgent(name="Writer"),
            AgentMetadata(name="Writer", capabilities=["writing", "content", "blog"]),
        )
        best_code = mgr._find_best_agent("write python code")
        assert best_code == "CodeBot"
        best_write = mgr._find_best_agent("write a blog post about AI")
        assert best_write == "Writer"
