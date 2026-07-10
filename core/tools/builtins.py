from __future__ import annotations

import datetime
import math
from typing import Any

import httpx

from core.tools.base import Tool, ToolResult


class CalculatorTool(Tool):
    name = "calculator"
    description = (
        "Evaluate a mathematical expression. Supports +, -, *, /, **, %, and common math functions."
    )
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Expression to evaluate, e.g. '2 + 2' or 'sqrt(144)'",
            }
        },
        "required": ["expression"],
    }

    async def execute(self, expression: str, **kwargs: Any) -> ToolResult:  # pyright: ignore[reportIncompatibleMethodOverride]
        allowed = set("0123456789.+-*/%()[] ,e")
        safe = all(c in allowed or c.isalpha() for c in expression)
        if not safe:
            return ToolResult(success=False, error="Expression contains disallowed characters")
        try:
            ns = {"__builtins__": {}, "math": math}
            result = eval(expression, ns)
            return ToolResult(success=True, output=str(result), data={"result": result})
        except Exception as e:
            return ToolResult(success=False, error=f"Evaluation error: {e}")


class CurrentDateTimeTool(Tool):
    name = "current_datetime"
    description = "Get the current date and time in the local timezone."
    parameters = {
        "type": "object",
        "properties": {},
    }

    async def execute(self, **kwargs: Any) -> ToolResult:  # pyright: ignore[reportIncompatibleMethodOverride]
        now = datetime.datetime.now().isoformat()
        return ToolResult(success=True, output=now, data={"datetime": now, "timezone": "local"})


class WebFetchTool(Tool):
    name = "web_fetch"
    description = "Fetch the content of a URL and return it as text."
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The URL to fetch"},
        },
        "required": ["url"],
    }

    async def execute(self, url: str, **kwargs: Any) -> ToolResult:  # pyright: ignore[reportIncompatibleMethodOverride]
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                text = resp.text[:5000]
                return ToolResult(
                    success=True,
                    output=text,
                    data={"status_code": resp.status_code, "url": url},
                )
        except Exception as e:
            return ToolResult(success=False, error=f"Fetch error: {e}")


class FileReadTool(Tool):
    name = "file_read"
    description = "Read the contents of a file at the given path."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute path to the file"},
            "limit": {"type": "integer", "description": "Max characters to read (default 5000)"},
        },
        "required": ["path"],
    }

    async def execute(self, path: str, limit: int = 5000, **kwargs: Any) -> ToolResult:  # pyright: ignore[reportIncompatibleMethodOverride]
        try:
            with open(path) as f:
                content = f.read(limit)
            return ToolResult(
                success=True,
                output=content,
                data={"path": path, "size": len(content)},
            )
        except Exception as e:
            return ToolResult(success=False, error=f"File read error: {e}")


DEFAULT_TOOLS: list[Tool] = [
    CalculatorTool(),
    CurrentDateTimeTool(),
    WebFetchTool(),
    FileReadTool(),
]
