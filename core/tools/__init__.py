"""Tool execution — timeout, retry, caching, and parallel execution.

Executes tools with configurable timeout and retry policies,
TTL-based result caching, parallel batch execution, and
execution statistics tracking.
"""

from core.tools.base import Tool, ToolResult
from core.tools.builtins import (
    DEFAULT_TOOLS,
    CalculatorTool,
    CurrentDateTimeTool,
    FileReadTool,
    WebFetchTool,
)
from core.tools.executor import ToolExecutor
from core.tools.registry import ToolRegistry

__all__ = [
    "Tool",
    "ToolResult",
    "ToolRegistry",
    "ToolExecutor",
    "DEFAULT_TOOLS",
    "CalculatorTool",
    "CurrentDateTimeTool",
    "WebFetchTool",
    "FileReadTool",
]
