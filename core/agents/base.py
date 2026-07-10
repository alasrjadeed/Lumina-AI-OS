from __future__ import annotations

import traceback

from pydantic import BaseModel

from core.provider import engine
from core.tools.registry import ToolRegistry


class AgentResult(BaseModel):
    agent_name: str
    status: str
    output: str
    error: str | None = None


class BaseAgent:
    name: str = "base"
    system_prompt: str = "You are a helpful AI assistant."

    def __init__(
        self,
        name: str | None = None,
        system_prompt: str | None = None,
        tool_registry: ToolRegistry | None = None,
    ):
        if name is not None:
            self.name = name
        if system_prompt is not None:
            self.system_prompt = system_prompt
        self.tool_registry = tool_registry

    async def run(self, task: str, context: dict | None = None) -> AgentResult:
        try:
            messages = [
                {"role": "system", "content": self.build_system_prompt(context)},
                {"role": "user", "content": task},
            ]
            tools = self.tool_registry.to_openai_tools() if self.tool_registry else None
            result = await engine.chat(messages, tools=tools)

            if "tool_calls" in result["message"] and result["message"]["tool_calls"]:
                messages.append(result["message"])
                for tc in result["message"]["tool_calls"]:
                    fn = tc.get("function", {})
                    name = fn.get("name", "")
                    args = fn.get("arguments", "{}")
                    assert self.tool_registry is not None
                    tool_result = await self.tool_registry.execute_call(name, args)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.get("id", ""),
                            "content": tool_result.output or tool_result.error or "",
                        }
                    )
                final = await engine.chat(messages)
                output = final["message"]["content"]
            else:
                output = result["message"]["content"]

            return AgentResult(
                agent_name=self.name,
                status="success",
                output=output,
            )
        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                status="error",
                output="",
                error=f"{type(e).__name__}: {e}\n{traceback.format_exc()}",
            )

    def build_system_prompt(self, context: dict | None = None) -> str:
        return self.system_prompt
