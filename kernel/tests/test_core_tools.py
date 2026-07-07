from __future__ import annotations

import pytest

from core.tools.base import Tool, ToolResult
from core.tools.builtins import DEFAULT_TOOLS, CalculatorTool, CurrentDateTimeTool, FileReadTool
from core.tools.registry import ToolRegistry


class EchoTool(Tool):
    name = "echo"
    description = "Echo back the input"
    parameters = {
        "type": "object",
        "properties": {
            "message": {"type": "string"},
        },
        "required": ["message"],
    }

    async def execute(self, message: str = "", **kwargs) -> ToolResult:
        return ToolResult(success=True, output=message, data={"echoed": message})


class FailTool(Tool):
    name = "fail"
    description = "Always fails"
    parameters = {"type": "object", "properties": {}}

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=False, error="intentional failure")


class TestTool:
    @pytest.mark.asyncio
    async def test_echo_tool(self):
        tool = EchoTool()
        result = await tool.execute(message="hello")
        assert result.success
        assert result.output == "hello"
        assert result.data == {"echoed": "hello"}

    @pytest.mark.asyncio
    async def test_fail_tool(self):
        tool = FailTool()
        result = await tool.execute()
        assert not result.success
        assert result.error == "intentional failure"

    @pytest.mark.asyncio
    async def test_to_openai_tool(self):
        tool = EchoTool()
        spec = tool.to_openai_tool()
        assert spec["type"] == "function"
        assert spec["function"]["name"] == "echo"
        assert spec["function"]["description"] == "Echo back the input"
        assert "parameters" in spec["function"]

    def test_tool_repr(self):
        assert repr(EchoTool()) == "Tool(name='echo')"


class TestCalculatorTool:
    @pytest.mark.asyncio
    async def test_addition(self):
        tool = CalculatorTool()
        result = await tool.execute(expression="2 + 2")
        assert result.success
        assert result.output == "4"
        assert result.data["result"] == 4

    @pytest.mark.asyncio
    async def test_division_by_zero(self):
        tool = CalculatorTool()
        result = await tool.execute(expression="1 / 0")
        assert not result.success

    @pytest.mark.asyncio
    async def test_math_functions(self):
        tool = CalculatorTool()
        result = await tool.execute(expression="math.sqrt(144)")
        assert result.success
        assert result.data["result"] == 12.0

    @pytest.mark.asyncio
    async def test_disallowed_chars(self):
        tool = CalculatorTool()
        result = await tool.execute(expression="__import__('os').system('ls')")
        assert not result.success
        assert "disallowed" in result.error


class TestCurrentDateTimeTool:
    @pytest.mark.asyncio
    async def test_datetime_output(self):
        tool = CurrentDateTimeTool()
        result = await tool.execute()
        assert result.success
        assert "T" in result.output
        assert result.data["timezone"] == "local"


class TestToolRegistry:
    def test_register_and_list(self):
        reg = ToolRegistry()
        reg.register(EchoTool())
        assert len(reg.list()) == 1
        assert reg.names() == ["echo"]

    def test_register_duplicate(self):
        reg = ToolRegistry()
        reg.register(EchoTool())
        with pytest.raises(ValueError, match="already registered"):
            reg.register(EchoTool())

    def test_get(self):
        reg = ToolRegistry()
        reg.register(EchoTool())
        assert reg.get("echo") is not None
        assert reg.get("nonexistent") is None

    def test_unregister(self):
        reg = ToolRegistry()
        reg.register(EchoTool())
        reg.unregister("echo")
        assert reg.get("echo") is None

    def test_to_openai_tools(self):
        reg = ToolRegistry()
        reg.register(EchoTool())
        tools = reg.to_openai_tools()
        assert len(tools) == 1
        assert tools[0]["function"]["name"] == "echo"

    @pytest.mark.asyncio
    async def test_execute_call(self):
        reg = ToolRegistry()
        reg.register(EchoTool())
        result = await reg.execute_call("echo", {"message": "hi"})
        assert result.success
        assert result.output == "hi"

    @pytest.mark.asyncio
    async def test_execute_call_string_args(self):
        reg = ToolRegistry()
        reg.register(EchoTool())
        result = await reg.execute_call("echo", '{"message": "hi"}')
        assert result.success
        assert result.output == "hi"

    @pytest.mark.asyncio
    async def test_execute_call_unknown(self):
        reg = ToolRegistry()
        result = await reg.execute_call("unknown", {})
        assert not result.success
        assert "Unknown tool" in result.error


class TestDefaultTools:
    def test_default_tools_loaded(self):
        names = [t.name for t in DEFAULT_TOOLS]
        assert "calculator" in names
        assert "current_datetime" in names
        assert "web_fetch" in names
        assert "file_read" in names


class TestFileReadTool:
    @pytest.mark.asyncio
    async def test_file_not_found(self):
        tool = FileReadTool()
        result = await tool.execute(path="/tmp/nonexistent_file_for_testing_xyz.txt")
        assert not result.success
        assert "error" in result.error.lower() or result.error
