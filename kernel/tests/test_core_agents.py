from __future__ import annotations

import pytest

from core.agents.base import AgentResult, BaseAgent
from core.tools.base import Tool, ToolResult
from core.tools.registry import ToolRegistry


class TestAgentResult:
    def test_success_result(self):
        r = AgentResult(agent_name="test", status="success", output="done")
        assert r.agent_name == "test"
        assert r.status == "success"
        assert r.output == "done"
        assert r.error is None

    def test_error_result(self):
        r = AgentResult(agent_name="test", status="error", output="", error="something broke")
        assert r.status == "error"
        assert r.error == "something broke"


class MockTool(Tool):
    name = "mock"
    description = "Mock tool for testing"
    parameters = {
        "type": "object",
        "properties": {
            "x": {"type": "integer"},
        },
    }

    async def execute(self, x: int = 0, **kwargs) -> ToolResult:
        return ToolResult(success=True, output=str(x * 2))


class TestBaseAgent:
    @pytest.mark.asyncio
    async def test_agent_no_tools(self):
        agent = BaseAgent(name="TestBot")
        result = await agent.run("say hello")
        assert result.status == "success"
        assert len(result.output) > 0

    @pytest.mark.asyncio
    async def test_agent_with_tools(self):
        reg = ToolRegistry()
        reg.register(MockTool())
        agent = BaseAgent(name="ToolBot", tool_registry=reg)
        result = await agent.run("use the mock tool with x=5")
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_build_system_prompt(self):
        agent = BaseAgent(name="TestBot", system_prompt="Custom prompt")
        assert agent.build_system_prompt() == "Custom prompt"
        assert agent.build_system_prompt({"key": "val"}) == "Custom prompt"

    def test_default_system_prompt(self):
        agent = BaseAgent(name="TestBot")
        assert agent.system_prompt == "You are a helpful AI assistant."

    def test_custom_name_init(self):
        agent = BaseAgent(name="CustomName")
        assert agent.name == "CustomName"
