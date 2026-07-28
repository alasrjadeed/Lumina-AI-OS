import asyncio
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Callable

from core.log import log
from core.goals import GoalStore
from core.provider import engine as ai_engine
from core.memory.store import memory as memory_store
from core.tool_framework import ToolFramework
from core.agent_chaining import ChainStore
from core.agent_builder import BlueprintStore
from core.task_manager import task_manager

SYSTEM_PROMPT = """You are the Brain of Lumina AI OS — a proactive, autonomous orchestrator.

Your role: Think → Observe → Command

1. OBSERVE: You receive a snapshot of the entire system — active goals, memory state,
   running tasks, agent health, and recent events.

2. THINK: Analyze the state. Identify:
   - What needs attention (blocked tasks, overdue goals, errors)
   - What can be optimized (idle agents, underutilized tools)
   - What should be done next (new goals, chained actions)
   - Priority order based on urgency and impact

3. COMMAND: Output structured decisions as a JSON array of commands.

Available commands:
- create_goal(name, description, priority) — create a new goal
- update_goal(goal_id, status) — update goal status (active|completed|blocked)
- create_todo(goal_id, description, priority) — add todo to a goal
- run_tool(tool_name, **kwargs) — execute a tool
- run_chain(chain_id) — execute an agent chain
- run_employee(goal_description) — run autonomous employee
- notify(message) — send a system notification
- adjust_settings(key, value) — adjust a system setting
- schedule(interval, action) — schedule a recurring action

Think step by step. Output ONLY a valid JSON array of command objects.
Each command must have: {"command": "command_name", "reason": "why", "params": {...}}
"""


@dataclass
class Thought:
    id: str
    timestamp: float
    observation: dict
    analysis: str
    commands: list[dict]
    executed: bool = False
    results: list[Any] = None

    def to_dict(self):
        return asdict(self)


class Brain:
    def __init__(self):
        self.goals = GoalStore()
        self.tools = ToolFramework()
        self.chains = ChainStore()
        self.blueprints = BlueprintStore()
        self.thinking_interval = 120
        self._thoughts: list[Thought] = []
        self._running = False
        self._task: asyncio.Task | None = None
        self._thinking_count = 0

    async def observe(self) -> dict:
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "goals": [],
            "system": {},
            "tasks": {},
            "tools": [],
            "memory": {},
        }

        try:
            goals_data = self.goals.list_goals()
            snapshot["goals"] = [
                {"id": g.id, "title": g.title, "status": g.status.value if hasattr(g.status, 'value') else str(g.status)}
                for g in goals_data
            ]
        except Exception as e:
            snapshot["goals"] = {"error": str(e)}

        try:
            snapshot["system"] = {
                "agent_count": len(self.blueprints.list()),
                "chain_count": len(self.chains.list()),
                "tool_count": len(self.tools.list_tools()),
            }
        except Exception as e:
            snapshot["system"]["error"] = str(e)

        try:
            stats = task_manager.get_stats()
            snapshot["tasks"] = {
                "active": stats.get("active", 0),
                "queued": stats.get("queued", 0),
                "completed": stats.get("completed", 0),
                "failed": stats.get("failed", 0),
            }
        except Exception as e:
            snapshot["tasks"]["error"] = str(e)

        try:
            tools_list = self.tools.list_tools()
            snapshot["tools"] = [
                {"name": t.get("name", "?"), "usage": t.get("usage_count", 0)}
                for t in (tools_list if isinstance(tools_list, list) else [])
            ]
        except Exception as e:
            snapshot["tools"] = {"error": str(e)}

        try:
            mem_stats = memory_store.get_stats() if hasattr(memory_store, 'get_stats') else {}
            snapshot["memory"] = mem_stats
        except Exception as e:
            snapshot["memory"] = {"error": str(e)}

        return snapshot

    async def think(self, observation: dict | None = None) -> Thought:
        if observation is None:
            observation = await self.observe()

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Current system state:\n```json\n{json.dumps(observation, indent=2, default=str)}\n```"}
        ]

        try:
            response = await ai_engine.chat(messages=messages, provider="deepseek", max_tokens=8192)
            content = response.get("message", response).get("content", "")
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            commands = json.loads(content)
            if isinstance(commands, dict):
                commands = [commands]
        except Exception as e:
            content = f"Parse error: {e}"
            commands = []

        thought = Thought(
            id=f"thought_{self._thinking_count}_{int(time.time())}",
            timestamp=time.time(),
            observation=observation,
            analysis=content if isinstance(content, str) else json.dumps(commands),
            commands=commands if isinstance(commands, list) else [],
        )
        self._thoughts.append(thought)
        self._thinking_count += 1
        return thought

    async def command(self, cmd: dict) -> Any:
        name = cmd.get("command", "")
        params = cmd.get("params", {})
        reason = cmd.get("reason", "")

        log.info("Brain command: %s — %s", name, reason)

        try:
            if name == "create_goal":
                return self.goals.create_goal(
                    title=params.get("name") or params.get("title", "Untitled"),
                    description=params.get("description", ""),
                )
            elif name == "update_goal":
                return self.goals.update_goal(
                    goal_id=params["goal_id"],
                    status=params.get("status"),
                )
            elif name == "create_todo":
                return self.goals.create_todo(
                    goal_id=params["goal_id"],
                    description=params.get("description", ""),
                )
            elif name == "run_tool":
                tool_name = params.pop("tool_name", params.get("name"))
                return self.tools.execute(tool_name, **params)
            elif name == "run_chain":
                return {"chain": params.get("chain_id"), "status": "triggered"}
            elif name == "run_employee":
                from core.employee.orchestrator import AutonomousEmployee
                employee = AutonomousEmployee()
                result = await employee.execute(params.get("goal_description", ""))
                return result
            elif name == "notify":
                log.info("Brain notification: %s", params.get("message", ""))
                return {"notified": params.get("message", "")}
            elif name == "adjust_settings":
                return {"setting": params.get("key"), "value": params.get("value"), "status": "applied"}
            elif name == "schedule":
                return {"interval": params.get("interval"), "action": params.get("action"), "status": "scheduled"}
            else:
                return {"error": f"Unknown command: {name}"}
        except Exception as e:
            log.error("Brain command failed: %s — %s", name, e)
            return {"error": str(e), "command": name}

    async def think_and_command(self) -> Thought:
        thought = await self.think()
        for cmd in thought.commands:
            result = await self.command(cmd)
            if thought.results is None:
                thought.results = []
            thought.results.append(result)
        thought.executed = True
        return thought

    async def loop(self, on_thought: Callable[[Thought], Any] | None = None):
        self._running = True
        log.info("Brain loop started (interval=%ss)", self.thinking_interval)
        while self._running:
            try:
                thought = await self.think_and_command()
                if on_thought:
                    await on_thought(thought)
                log.info("Brain cycle complete: %d commands", len(thought.commands))
            except Exception as e:
                log.error("Brain cycle error: %s", e)
            await asyncio.sleep(self.thinking_interval)

    def stop(self):
        self._running = False
        log.info("Brain loop stopped")

    @property
    def status(self) -> dict:
        return {
            "running": self._running,
            "thinking_interval": self.thinking_interval,
            "total_thoughts": len(self._thoughts),
            "last_thought": self._thoughts[-1].to_dict() if self._thoughts else None,
        }

    @property
    def history(self) -> list[dict]:
        return [t.to_dict() for t in self._thoughts[-50:]]


brain = Brain()
