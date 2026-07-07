"""Autonomous Employee v2 — multi-tool AI employee with persistent memory, web search, code execution, and real-time streaming.

You say: "Research competitors and write a comparison report"
It does: web search → read pages → analyze → write report → save file → notify you
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator

from core.log import log
from core.provider import engine

MEMORY_FILE = os.path.expanduser("~/.lumina/employee_memory.json")


# ── Data Models ──

@dataclass
class ToolCall:
    tool: str
    args: dict[str, Any] = field(default_factory=dict)
    result: Any = None
    status: str = "running"
    error: str = ""
    started: float = 0.0
    completed: float = 0.0

@dataclass
class MissionStep:
    id: str = ""
    name: str = ""
    description: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    status: str = "pending"
    result: Any = None
    error: str = ""
    started: float = 0.0
    completed: float = 0.0

@dataclass
class Mission:
    id: str = ""
    goal: str = ""
    steps: list[MissionStep] = field(default_factory=list)
    status: str = "planning"
    summary: str = ""
    report: str = ""
    created: float = field(default_factory=time.time)
    completed: float = 0.0


# ── Memory ──

def load_memory() -> dict:
    try:
        f = Path(MEMORY_FILE)
        if f.exists():
            return json.loads(f.read_text())
    except: pass
    return {"missions": [], "knowledge": {}, "preferences": {}, "contexts": {}}

def save_memory(data: dict):
    Path(MEMORY_FILE).parent.mkdir(parents=True, exist_ok=True)
    Path(MEMORY_FILE).write_text(json.dumps(data, indent=2))


# ── Tools ──

TOOLS = {
    "web_search": {
        "name": "web_search",
        "description": "Search the web for information. Returns top results with snippets.",
        "parameters": {"query": "string (required)", "count": "int (optional, default 5)"},
    },
    "web_fetch": {
        "name": "web_fetch",
        "description": "Fetch and read the content of a web page.",
        "parameters": {"url": "string (required)"},
    },
    "execute_code": {
        "name": "execute_code",
        "description": "Execute Python code. Use for data analysis, file processing, automation.",
        "parameters": {"code": "string (required) — Python code to execute"},
    },
    "shell_command": {
        "name": "shell_command",
        "description": "Run any shell command on the server.",
        "parameters": {"command": "string (required) — shell command"},
    },
    "read_file": {
        "name": "read_file",
        "description": "Read the contents of a file.",
        "parameters": {"path": "string (required) — file path"},
    },
    "write_file": {
        "name": "write_file",
        "description": "Write content to a file. Creates directories if needed.",
        "parameters": {"path": "string (required)", "content": "string (required)"},
    },
    "list_dir": {
        "name": "list_dir",
        "description": "List files and folders in a directory.",
        "parameters": {"path": "string (required) — directory path"},
    },
    "remember": {
        "name": "remember",
        "description": "Store a fact or piece of information in long-term memory.",
        "parameters": {"key": "string (required)", "value": "string (required)"},
    },
    "recall": {
        "name": "recall",
        "description": "Retrieve information from long-term memory.",
        "parameters": {"key": "string (required)"},
    },
    "send_notification": {
        "name": "send_notification",
        "description": "Send a desktop notification to the user.",
        "parameters": {"title": "string (required)", "message": "string (required)"},
    },
}


# ── Agent ──

class AutonomousEmployee:
    """Upgraded autonomous employee with real tool calling, memory, and streaming."""

    def __init__(self):
        self._missions: list[Mission] = []
        self._progress_callbacks: list = []

    def on_progress(self, cb):
        self._progress_callbacks.append(cb)

    async def _emit(self, data: dict):
        for cb in self._progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(data)
                else:
                    cb(data)
            except Exception as e:
                log.error("Employee: callback error: %s", e)

    async def execute(self, goal: str) -> dict:
        """Execute a goal with full tool access and memory."""
        memory = load_memory()
        mission = Mission(id=f"mission_{int(time.time())}", goal=goal)
        mission.created = time.time()

        await self._emit({"type": "status", "message": "Planning mission...", "mission_id": mission.id})

        # Plan
        plan = await self._plan(goal, memory)
        mission.summary = plan.get("summary", goal[:100])
        steps_data = plan.get("steps", [])
        mission.steps = [MissionStep(**s) for s in steps_data]
        mission.status = "running"

        await self._emit({
            "type": "plan",
            "summary": mission.summary,
            "steps": [{"id": s.id, "name": s.name, "description": s.description} for s in mission.steps],
            "mission_id": mission.id,
        })

        # Execute each step
        for step in mission.steps:
            step.status = "running"
            step.started = time.time()

            await self._emit({
                "type": "step_start",
                "step_id": step.id,
                "name": step.name,
                "description": step.description,
            })

            try:
                result = await self._execute_step(step, memory)
                step.result = result
                step.status = "success"
                step.completed = time.time()
                await self._emit({
                    "type": "step_complete",
                    "step_id": step.id,
                    "name": step.name,
                    "status": "success",
                    "result": str(result)[:500],
                    "tool_calls": [
                        {"tool": tc.tool, "args": tc.args, "result": str(tc.result)[:300], "status": tc.status}
                        for tc in step.tool_calls
                    ],
                })
            except Exception as e:
                step.status = "failed"
                step.error = str(e)
                step.completed = time.time()
                await self._emit({
                    "type": "step_complete",
                    "step_id": step.id,
                    "name": step.name,
                    "status": "failed",
                    "error": str(e),
                })

        # Report
        mission.status = "completed"
        mission.completed = time.time()

        # Save memory
        memory.setdefault("missions", []).append({
            "id": mission.id,
            "goal": mission.goal,
            "summary": mission.summary,
            "completed": mission.completed,
            "success": all(s.status == "success" for s in mission.steps),
        })
        save_memory(memory)

        report = await self._generate_report(goal, mission)
        mission.report = report

        await self._emit({
            "type": "mission_complete",
            "mission_id": mission.id,
            "summary": mission.summary,
            "report": report,
            "duration": mission.completed - mission.created,
            "steps_total": len(mission.steps),
            "steps_ok": sum(1 for s in mission.steps if s.status == "success"),
        })

        return {
            "id": mission.id,
            "goal": goal,
            "summary": mission.summary,
            "steps": [
                {
                    "id": s.id, "name": s.name, "description": s.description,
                    "status": s.status, "error": s.error,
                    "tool_calls": [
                        {"tool": tc.tool, "args": tc.args, "result": str(tc.result)[:300], "status": tc.status}
                        for tc in s.tool_calls
                    ],
                }
                for s in mission.steps
            ],
            "report": report,
            "duration_seconds": round(mission.completed - mission.created, 1),
            "memory_updated": True,
        }

    async def _plan(self, goal: str, memory: dict) -> dict:
        tools_desc = "\n".join([
            f"- {t['name']}: {t['description']} Params: {json.dumps(t['parameters'])}"
            for t in TOOLS.values()
        ])
        context = memory.get("contexts", {}).get("current", "")
        knowledge = memory.get("knowledge", {})

        prompt = f"""You are an autonomous AI employee. Break down this goal into steps.

GOAL: {goal}

CONTEXT: {context or 'None'}
KNOWN FACTS: {json.dumps(knowledge, indent=2)[:500] or 'None'}

AVAILABLE TOOLS:
{tools_desc}

Rules:
- Each step should make 1-3 tool calls
- Use web_search and web_fetch for research
- Use execute_code for data processing
- Use shell_command for system tasks
- Use remember to save important facts
- Use send_notification to alert the user
- Keep steps practical and sequential

Return JSON:
{{"summary": "brief plan",
 "steps": [
   {{"id": "1", "name": "Research competitors", "description": "Search web for competitor info",
     "tool_calls": [{{"tool": "web_search", "args": {{"query": "..."}}}}]}}
 ]}}

Make 3-8 steps. Be specific with tool arguments."""
        try:
            resp = await engine.chat([{"role": "user", "content": prompt}])
            text = resp.get("message", {}).get("content", "")
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            log.error("Employee: Plan error: %s", e)
        return {"summary": goal, "steps": [{"id": "1", "name": goal, "description": goal, "tool_calls": []}]}

    async def _execute_step(self, step: MissionStep, memory: dict) -> Any:
        results = []
        for tc_data in (step.tool_calls if hasattr(step, 'tool_calls') else []):
            tool = tc_data.get("tool") if isinstance(tc_data, dict) else tc_data.tool
            args = tc_data.get("args", {}) if isinstance(tc_data, dict) else tc_data.args

            tc = ToolCall(tool=tool, args=args, started=time.time())
            step.tool_calls.append(tc)

            await self._emit({
                "type": "tool_call",
                "step_id": step.id,
                "tool": tool,
                "args": args,
            })

            try:
                result = await self._run_tool(tool, args, memory)
                tc.result = result
                tc.status = "success"
                tc.completed = time.time()
                results.append({"tool": tool, "result": str(result)[:500]})
                await self._emit({
                    "type": "tool_result",
                    "step_id": step.id,
                    "tool": tool,
                    "result": str(result)[:500],
                    "status": "success",
                })
            except Exception as e:
                tc.status = "failed"
                tc.error = str(e)
                tc.completed = time.time()
                results.append({"tool": tool, "error": str(e)})
                await self._emit({
                    "type": "tool_result",
                    "step_id": step.id,
                    "tool": tool,
                    "error": str(e),
                    "status": "failed",
                })

        return results

    async def _run_tool(self, tool: str, args: dict, memory: dict) -> Any:
        if tool == "web_search":
            return await self._web_search(args.get("query", ""), args.get("count", 5))
        elif tool == "web_fetch":
            return await self._web_fetch(args.get("url", ""))
        elif tool == "execute_code":
            return await self._execute_code(args.get("code", ""))
        elif tool == "shell_command":
            return await self._shell(args.get("command", ""))
        elif tool == "read_file":
            return await self._read_file(args.get("path", ""))
        elif tool == "write_file":
            return await self._write_file(args.get("path", ""), args.get("content", ""))
        elif tool == "list_dir":
            return await self._list_dir(args.get("path", "."))
        elif tool == "remember":
            memory["knowledge"][args["key"]] = args["value"]
            save_memory(memory)
            return f"Remembered: {args['key']} = {args['value'][:100]}"
        elif tool == "recall":
            return memory.get("knowledge", {}).get(args.get("key", ""), "Not found")
        elif tool == "send_notification":
            return await self._notify(args.get("title", "Employee"), args.get("message", ""))
        return f"Unknown tool: {tool}"

    async def _web_search(self, query: str, count: int = 5) -> list[dict]:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                results = []
                for match in re.finditer(
                    r'<a rel="nofollow" class="result__a" href="(.*?)".*?>(.*?)</a>.*?class="result__snippet".*?>(.*?)</',
                    resp.text, re.DOTALL,
                ):
                    results.append({
                        "url": match.group(1),
                        "title": re.sub(r"<.*?>", "", match.group(2)),
                        "snippet": re.sub(r"<.*?>", "", match.group(3)),
                    })
                    if len(results) >= count:
                        break
                return results
        except Exception as e:
            return [{"error": str(e)}]

    async def _web_fetch(self, url: str) -> str:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                text = re.sub(r"<script.*?>.*?</script>", "", resp.text, flags=re.DOTALL)
                text = re.sub(r"<style.*?>.*?</style>", "", text, flags=re.DOTALL)
                text = re.sub(r"<.*?>", " ", text)
                text = re.sub(r"\s+", " ", text).strip()
                return text[:5000]
        except Exception as e:
            return f"Error fetching {url}: {e}"

    async def _execute_code(self, code: str) -> str:
        try:
            result = subprocess.run(
                ["python", "-c", code],
                capture_output=True, text=True, timeout=30,
            )
            output = result.stdout or result.stderr
            return output[:2000] or "Code executed (no output)"
        except subprocess.TimeoutExpired:
            return "Code execution timed out"
        except Exception as e:
            return f"Execution error: {e}"

    async def _shell(self, command: str) -> dict:
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return {
                "stdout": result.stdout[:1000],
                "stderr": result.stderr[:500],
                "return_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"error": "Timed out"}
        except Exception as e:
            return {"error": str(e)}

    async def _read_file(self, path: str) -> str:
        p = Path(path).expanduser()
        if p.exists() and p.is_file():
            return p.read_text()[:5000]
        return f"File not found: {path}"

    async def _write_file(self, path: str, content: str) -> str:
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"Written {len(content)} bytes to {path}"

    async def _list_dir(self, path: str) -> list[dict]:
        p = Path(path).expanduser()
        if not p.exists():
            return [{"error": f"Not found: {path}"}]
        items = []
        for e in p.iterdir():
            items.append({
                "name": e.name,
                "type": "dir" if e.is_dir() else "file",
                "size": e.stat().st_size if e.is_file() else 0,
            })
        return items

    async def _notify(self, title: str, message: str) -> str:
        try:
            subprocess.run(
                ["notify-send", title, message],
                capture_output=True, timeout=5,
            )
            return f"Notification sent: {title}"
        except:
            return f"Notification system not available: {title}: {message}"

    async def _generate_report(self, goal: str, mission: Mission) -> str:
        steps_summary = "\n".join([
            f"{'✅' if s.status == 'success' else '❌'} {s.name}: {str(s.result)[:200] if s.result else s.error}"
            for s in mission.steps
        ])
        prompt = f"""Generate a concise mission report.

GOAL: {goal}

STEPS:
{steps_summary}

Write a brief 3-5 sentence report covering what was accomplished, any failures, and what was learned."""
        try:
            resp = await engine.chat([{"role": "user", "content": prompt}])
            return resp.get("message", {}).get("content", "Mission completed.")
        except:
            return "Mission completed. Check details above."

    def get_history(self, limit: int = 10) -> list[dict]:
        memory = load_memory()
        return memory.get("missions", [])[-limit:]

    def get_memory(self) -> dict:
        return load_memory()


employee = AutonomousEmployee()
