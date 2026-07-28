from __future__ import annotations

import json
import math
import subprocess
import time
import urllib.parse
import urllib.request
from typing import Any, Callable


class Tool:
    def __init__(self, name: str, description: str, fn: Callable, parameters: list[dict] | None = None):
        self.name = name
        self.description = description
        self.fn = fn
        self.parameters = parameters or []
        self.usage_count = 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "usage_count": self.usage_count,
        }

    def execute(self, **kwargs) -> dict:
        self.usage_count += 1
        start = time.time()
        try:
            result = self.fn(**kwargs)
            elapsed = time.time() - start
            return {"success": True, "result": result, "elapsed_ms": round(elapsed * 1000)}
        except Exception as e:
            elapsed = time.time() - start
            return {"success": False, "error": str(e), "elapsed_ms": round(elapsed * 1000)}


class ToolFramework:
    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register(Tool("calculator", "Evaluate a mathematical expression", self._calc, [
            {"name": "expression", "type": "string", "description": "Math expression (e.g. 2 + 2 * 3)", "required": True},
        ]))
        self.register(Tool("web_search", "Search the web for information", self._web_search, [
            {"name": "query", "type": "string", "description": "Search query", "required": True},
            {"name": "max_results", "type": "integer", "description": "Max results (default 5)", "required": False},
        ]))
        self.register(Tool("json_parse", "Parse and validate JSON string", self._json_parse, [
            {"name": "text", "type": "string", "description": "JSON string to parse", "required": True},
        ]))
        self.register(Tool("base64_encode", "Encode text to base64", lambda text: base64_encode(text), [
            {"name": "text", "type": "string", "description": "Text to encode", "required": True},
        ]))
        self.register(Tool("base64_decode", "Decode base64 to text", lambda text: base64_decode(text), [
            {"name": "text", "type": "string", "description": "Base64 string to decode", "required": True},
        ]))
        self.register(Tool("word_count", "Count words in text", lambda text: len(text.split()), [
            {"name": "text", "type": "string", "description": "Text to count words in", "required": True},
        ]))
        self.register(Tool("char_count", "Count characters in text", lambda text: len(text), [
            {"name": "text", "type": "string", "description": "Text to count characters in", "required": True},
        ]))
        self.register(Tool("uuid_gen", "Generate a UUID", lambda: __import__('uuid').uuid4().hex, []))
        self.register(Tool("timestamp", "Get current Unix timestamp", lambda: time.time(), []))
        self.register(Tool("echo", "Echo back the input (for testing)", lambda text: text, [
            {"name": "text", "type": "string", "description": "Text to echo", "required": True},
        ]))

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def list_tools(self) -> list[dict]:
        return [t.to_dict() for t in self._tools.values()]

    def get_tool(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def execute(self, name: str, **kwargs) -> dict:
        tool = self.get_tool(name)
        if not tool:
            return {"success": False, "error": f"Tool '{name}' not found"}
        return tool.execute(**kwargs)

    def get_stats(self) -> dict:
        total = sum(t.usage_count for t in self._tools.values())
        return {
            "total_tools": len(self._tools),
            "total_calls": total,
            "tools": {name: t.usage_count for name, t in self._tools.items()},
        }

    def _calc(self, expression: str) -> float:
        safe = expression.replace(" ", "")
        allowed = set("0123456789+-*/.()%")
        if not all(c in allowed for c in safe):
            raise ValueError("Expression contains disallowed characters")
        return eval(safe, {"__builtins__": {}}, {"math": math})

    def _json_parse(self, text: str) -> dict:
        return json.loads(text)

    def _web_search(self, query: str, max_results: int = 5) -> list[dict]:
        try:
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1"
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read())
            results = []
            for topic in data.get("RelatedTopics", [])[:max_results]:
                if "Text" in topic:
                    results.append({"title": topic.get("Text", ""), "url": topic.get("FirstURL", "")})
            return results
        except Exception as e:
            return [{"error": str(e)}]


def base64_encode(text: str) -> str:
    import base64 as b64
    return b64.b64encode(text.encode()).decode()


def base64_decode(text: str) -> str:
    import base64 as b64
    return b64.b64decode(text.encode()).decode()


tool_framework = ToolFramework()
