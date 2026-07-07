"""Task Queue — chain multiple automation tasks into pipelines.

Instead of running tasks one by one, queue them all and execute sequentially.
Supports dependencies, parallel execution, retries, and progress tracking.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from core.log import log


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Task:
    """A single task in the queue."""
    id: str = ""
    name: str = ""
    action: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    module: str = "chat"
    depends_on: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str = ""
    created: float = field(default_factory=time.time)
    started: float = 0.0
    completed: float = 0.0
    duration_ms: float = 0.0
    retries: int = 0
    max_retries: int = 2


@dataclass
class Pipeline:
    """A pipeline is a named collection of tasks."""
    id: str = ""
    name: str = ""
    tasks: list[Task] = field(default_factory=list)
    status: str = "draft"
    created: float = field(default_factory=time.time)
    completed: float = 0.0


def _new_id() -> str:
    return uuid.uuid4().hex[:8]


# ── Task Executors — maps module.action to handler ──

async def _execute_chat(params: dict) -> str:
    from core.provider import engine
    resp = await engine.chat([{"role": "user", "content": params.get("prompt", "")}])
    return resp.get("message", {}).get("content", "")


async def _execute_content(params: dict) -> str:
    from core.writer.generator import writer
    result = await writer.generate(
        params.get("type", "blog"), params.get("topic", ""), params.get("tone", "professional"),
    )
    return result.get("content", "")


async def _execute_browser(params: dict) -> dict:
    from core.browser.agent import browser_agent
    return await browser_agent.execute(params.get("task", ""), headless=True)


async def _execute_whatsapp(params: dict) -> str:
    from core.whatsapp.client import whatsapp
    result = await whatsapp.send_text(params.get("to", ""), params.get("text", ""))
    return str(result)


async def _execute_social(params: dict) -> str:
    from core.social.manager import social
    p = social.create_post(params.get("content", ""), params.get("platform", "facebook"))
    return f"Post created: {p.id}"


async def _execute_crm(params: dict) -> str:
    from core.crm.pipeline import crm
    if params.get("action") == "add_contact":
        c = crm.add_contact(params.get("name", ""), params.get("email", ""))
        return f"Contact added: {c['id']}"
    if params.get("action") == "add_deal":
        d = crm.add_deal(params.get("title", ""), float(params.get("value", 0)), "")
        return f"Deal added: {d['id']}"
    if params.get("action") == "summary":
        return str(crm.get_sales_summary())
    return "CRM action completed"


async def _execute_vault(params: dict) -> str:
    from core.vault.store import vault
    if params.get("action") == "set":
        vault.set(params.get("key", ""), params.get("value", ""))
        return f"Saved: {params.get('key', '')}"
    return vault.to_context_prompt()


EXECUTORS: dict[str, Callable] = {
    "chat": _execute_chat,
    "content": _execute_content,
    "browser": _execute_browser,
    "whatsapp": _execute_whatsapp,
    "social": _execute_social,
    "crm": _execute_crm,
    "vault": _execute_vault,
}


class TaskQueue:
    """Queue and execute multi-step automation pipelines."""

    def __init__(self, storage_path: str = "task_queue.json"):
        self.storage_path = storage_path
        self._pipelines: list[Pipeline] = []
        self._active_tasks: dict[str, asyncio.Task] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
            for p in data.get("pipelines", []):
                tasks = [Task(**t) for t in p.get("tasks", [])]
                pipeline = Pipeline(id=p["id"], name=p["name"], tasks=tasks,
                                    status=p.get("status", "draft"), created=p.get("created", 0))
                self._pipelines.append(pipeline)
        except Exception:
            pass

    def _save(self) -> None:
        with open(self.storage_path, "w") as f:
            json.dump({
                "pipelines": [{"id": p.id, "name": p.name, "status": p.status,
                               "created": p.created, "completed": p.completed,
                               "tasks": [{"id": t.id, "name": t.name, "action": t.action,
                                          "params": t.params, "module": t.module,
                                          "depends_on": t.depends_on, "status": t.status.value,
                                          "result": str(t.result)[:200] if t.result else "",
                                          "error": t.error[:200], "created": t.created,
                                          "started": t.started, "completed": t.completed,
                                          "duration_ms": t.duration_ms, "retries": t.retries,
                                          "max_retries": t.max_retries}
                                         for t in p.tasks]}
                              for p in self._pipelines],
            }, f, indent=2)

    # ── Pipeline Management ──

    def create_pipeline(self, name: str) -> Pipeline:
        pipeline = Pipeline(id=_new_id(), name=name)
        self._pipelines.append(pipeline)
        self._save()
        return pipeline

    def add_task(self, pipeline_id: str, name: str, action: str,
                 module: str = "chat", params: dict | None = None,
                 depends_on: list[str] | None = None) -> Task | None:
        pipeline = next((p for p in self._pipelines if p.id == pipeline_id), None)
        if not pipeline:
            return None
        task = Task(
            id=_new_id(), name=name, action=action, module=module,
            params=params or {}, depends_on=depends_on or [],
        )
        pipeline.tasks.append(task)
        self._save()
        return task

    def get_pipeline(self, pipeline_id: str) -> Pipeline | None:
        return next((p for p in self._pipelines if p.id == pipeline_id), None)

    def list_pipelines(self) -> list[Pipeline]:
        return list(self._pipelines)

    def delete_pipeline(self, pipeline_id: str) -> bool:
        before = len(self._pipelines)
        self._pipelines = [p for p in self._pipelines if p.id != pipeline_id]
        if len(self._pipelines) < before:
            self._save()
            return True
        return False

    # ── Execution ──

    async def run_pipeline(self, pipeline_id: str) -> dict:
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            return {"error": "Pipeline not found"}

        pipeline.status = "running"
        results = []

        for task in pipeline.tasks:
            # Check dependencies
            deps_met = all(
                any(t.id in dep for t in pipeline.tasks if t.status == TaskStatus.SUCCESS)
                for dep in task.depends_on
            ) if task.depends_on else True

            if not deps_met:
                task.status = TaskStatus.SKIPPED
                results.append({"task": task.name, "status": "skipped", "reason": "dependency not met"})
                continue

            task.status = TaskStatus.RUNNING
            task.started = time.time()
            self._save()

            executor = EXECUTORS.get(task.module)
            if not executor:
                task.status = TaskStatus.FAILED
                task.error = f"No executor for module: {task.module}"
                results.append({"task": task.name, "status": "failed", "error": task.error})
                continue

            for attempt in range(task.max_retries + 1):
                try:
                    task.retries = attempt
                    result = await executor(task.params)
                    task.status = TaskStatus.SUCCESS
                    task.result = str(result)[:500]
                    task.completed = time.time()
                    task.duration_ms = (task.completed - task.started) * 1000
                    results.append({"task": task.name, "status": "success"})
                    break
                except Exception as e:
                    task.error = str(e)
                    if attempt < task.max_retries:
                        log.info("Task %s: retry %d/%d", task.name, attempt + 1, task.max_retries)
                        await asyncio.sleep(1)
                    else:
                        task.status = TaskStatus.FAILED
                        task.completed = time.time()
                        results.append({"task": task.name, "status": "failed", "error": str(e)})

            self._save()

        pipeline.status = "completed"
        pipeline.completed = time.time()
        self._save()

        return {"pipeline": pipeline.name, "tasks": len(pipeline.tasks), "results": results}

    async def run_all_pending(self) -> list[dict]:
        results = []
        for pipeline in self._pipelines:
            if pipeline.status == "draft":
                result = await self.run_pipeline(pipeline.id)
                results.append(result)
        return results

    # ── Stats ──

    def get_stats(self) -> dict:
        total = sum(len(p.tasks) for p in self._pipelines)
        completed = sum(1 for p in self._pipelines if p.status == "completed")
        running = sum(1 for p in self._pipelines if p.status == "running")
        return {
            "pipelines": len(self._pipelines),
            "total_tasks": total,
            "completed": completed,
            "running": running,
            "draft": sum(1 for p in self._pipelines if p.status == "draft"),
        }


queue = TaskQueue()
