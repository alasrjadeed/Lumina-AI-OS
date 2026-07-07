from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from typing import Any, Callable, Coroutine

from core.log import log
from core.task_manager.models import Task, TaskEvent, TaskPriority, TaskStatus, TaskStep


Handler = Callable[..., Coroutine[Any, Any, Any]]

STORAGE_PATH = "tasks_data.json"


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


class TaskManager:
    """Persistent, observable task manager with progress tracking, pause/resume/cancel.

    Features:
    - Persistent queue (JSON file)
    - Real-time progress (0-100%)
    - Pause / resume / cancel individual tasks
    - Event emission for SSE/polling consumers
    - Dependency-aware step execution
    - Retry with backoff
    - Task tagging and priority
    """

    def __init__(self, storage_path: str = STORAGE_PATH):
        self.storage_path = storage_path
        self._tasks: dict[str, Task] = {}
        self._active_runs: dict[str, asyncio.Task] = {}
        self._event_listeners: list[Callable[[TaskEvent], None]] = []
        self._handlers: dict[str, Handler] = {}
        self._paused: set[str] = set()
        self._cancelled: set[str] = set()
        self._load()

    # ── Persistence ──

    def _load(self) -> None:
        if not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
            for d in data.get("tasks", []):
                task = self._dict_to_task(d)
                self._tasks[task.id] = task
        except Exception as e:
            log.warning("TaskManager: failed to load: %s", e)

    def _save(self) -> None:
        try:
            with open(self.storage_path, "w") as f:
                json.dump({"tasks": [t.to_dict() for t in self._tasks.values()]}, f, indent=2, default=str)
        except Exception as e:
            log.warning("TaskManager: failed to save: %s", e)

    @staticmethod
    def _dict_to_task(d: dict) -> Task:
        steps = []
        for sd in d.get("steps", []):
            s = TaskStep(
                id=sd.get("id", _new_id()),
                name=sd.get("name", ""),
                agent=sd.get("agent", ""),
                description=sd.get("description", ""),
                params=sd.get("params", {}),
                depends_on=sd.get("depends_on", []),
                status=TaskStatus(sd.get("status", "pending")),
                progress=sd.get("progress", 0),
                progress_label=sd.get("progress_label", ""),
                result=sd.get("result"),
                error=sd.get("error", ""),
                started=sd.get("started", 0),
                completed=sd.get("completed", 0),
            )
            steps.append(s)
        task = Task(
            id=d.get("id", _new_id()),
            name=d.get("name", ""),
            description=d.get("description", ""),
            priority=TaskPriority[d.get("priority", "NORMAL")],
            tags=d.get("tags", []),
            status=TaskStatus(d.get("status", "pending")),
            progress=d.get("progress", 0),
            progress_label=d.get("progress_label", ""),
            steps=steps,
            result=d.get("result"),
            error=d.get("error", ""),
            created=d.get("created", 0),
            started=d.get("started", 0),
            completed=d.get("completed", 0),
            duration_ms=d.get("duration_ms", 0),
            max_retries=d.get("max_retries", 2),
            retry_count=d.get("retry_count", 0),
            schedule_at=d.get("schedule_at", 0),
            parent_id=d.get("parent_id", ""),
            metadata=d.get("metadata", {}),
        )
        return task

    # ── Event System ──

    def on_event(self, listener: Callable[[TaskEvent], None]) -> None:
        self._event_listeners.append(listener)

    def _emit(self, event: TaskEvent) -> None:
        for listener in self._event_listeners:
            try:
                listener(event)
            except Exception:
                pass

    # ── Handler Registration ──

    def register_handler(self, name: str, handler: Handler) -> None:
        self._handlers[name] = handler

    def register_handlers(self, handlers: dict[str, Handler]) -> None:
        self._handlers.update(handlers)

    # ── Task CRUD ──

    def create_task(
        self,
        name: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        tags: list[str] | None = None,
        max_retries: int = 2,
        metadata: dict | None = None,
    ) -> Task:
        task = Task(
            id=_new_id(),
            name=name,
            description=description,
            priority=priority,
            tags=tags or [],
            max_retries=max_retries,
            metadata=metadata or {},
        )
        self._tasks[task.id] = task
        self._emit(task.emit_event("task.created", message=f"Task created: {name}"))
        self._save()
        log.info("TaskManager: created task %s: %s", task.id, name)
        return task

    def add_step(self, task_id: str, name: str, agent: str = "",
                 description: str = "", params: dict | None = None,
                 depends_on: list[str] | None = None) -> TaskStep | None:
        task = self.get_task(task_id)
        if not task:
            return None
        step = TaskStep(
            id=_new_id(),
            name=name,
            agent=agent,
            description=description,
            params=params or {},
            depends_on=depends_on or [],
        )
        task.steps.append(step)
        self._save()
        return step

    def get_task(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def list_tasks(self, status: str | None = None, tag: str | None = None,
                   limit: int = 50, offset: int = 0) -> list[Task]:
        tasks = sorted(self._tasks.values(), key=lambda t: t.created, reverse=True)
        if status:
            tasks = [t for t in tasks if t.status.value == status]
        if tag:
            tasks = [t for t in tasks if tag in t.tags]
        return tasks[offset:offset + limit]

    def delete_task(self, task_id: str) -> bool:
        if task_id in self._active_runs:
            self._active_runs[task_id].cancel()
            del self._active_runs[task_id]
        task = self._tasks.pop(task_id, None)
        if task:
            self._save()
            return True
        return False

    def update_progress(self, task_id: str, progress: int, label: str = "") -> None:
        task = self.get_task(task_id)
        if not task:
            return
        task.progress = min(max(progress, 0), 100)
        if label:
            task.progress_label = label
        self._emit(task.emit_event("task.progress", message=label))
        self._save()

    def update_step_progress(self, task_id: str, step_id: str,
                              progress: int, label: str = "") -> None:
        task = self.get_task(task_id)
        if not task:
            return
        for step in task.steps:
            if step.id == step_id:
                step.progress = min(max(progress, 0), 100)
                if label:
                    step.progress_label = label
                break
        self._save()

    # ── Pause / Resume / Cancel ──

    def pause_task(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        if not task or task.status != TaskStatus.RUNNING:
            return False
        self._paused.add(task_id)
        task.status = TaskStatus.PAUSED
        task.progress_label = "Paused"
        self._emit(task.emit_event("task.paused", message="Task paused"))
        self._save()
        log.info("TaskManager: paused task %s", task_id)
        return True

    def resume_task(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        if not task or task.status != TaskStatus.PAUSED:
            return False
        self._paused.discard(task_id)
        task.status = TaskStatus.RUNNING
        task.progress_label = "Resumed"
        self._emit(task.emit_event("task.resumed", message="Task resumed"))
        self._save()
        log.info("TaskManager: resumed task %s", task_id)
        return True

    def cancel_task(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        if not task or task.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.FAILED):
            return False
        self._cancelled.add(task_id)
        self._paused.discard(task_id)
        task.status = TaskStatus.CANCELLED
        task.progress_label = "Cancelled"
        task.completed = time.time()
        for step in task.steps:
            if step.status == TaskStatus.RUNNING:
                step.status = TaskStatus.SKIPPED
        self._emit(task.emit_event("task.cancelled", message="Task cancelled"))
        self._save()
        if task_id in self._active_runs:
            self._active_runs[task_id].cancel()
        log.info("TaskManager: cancelled task %s", task_id)
        return True

    # ── Execution ──

    async def run_task(self, task_id: str) -> dict:
        task = self.get_task(task_id)
        if not task:
            return {"error": "Task not found"}

        if task_id in self._active_runs:
            return {"error": "Task already running"}

        self._cancelled.discard(task_id)
        self._paused.discard(task_id)

        run = asyncio.create_task(self._execute_task(task))
        self._active_runs[task_id] = run
        try:
            result = await run
        except asyncio.CancelledError:
            result = {"status": "cancelled"}
        finally:
            self._active_runs.pop(task_id, None)
        return result

    async def _execute_task(self, task: Task) -> dict:
        task.status = TaskStatus.RUNNING
        task.started = time.time()
        task.retry_count = 0
        self._emit(task.emit_event("task.started", message="Task started"))
        self._save()

        step_results = []

        for step in task.steps:
            if task.id in self._cancelled:
                step.status = TaskStatus.SKIPPED
                step_results.append({"step": step.name, "status": "cancelled"})
                continue

            while task.id in self._paused:
                await asyncio.sleep(0.5)

            deps_ok = self._check_dependencies(task, step)
            if not deps_ok:
                step.status = TaskStatus.SKIPPED
                step_results.append({"step": step.name, "status": "skipped", "reason": "dependency not met"})
                self._save()
                continue

            step.status = TaskStatus.RUNNING
            step.started = time.time()
            self._emit(task.emit_event("step.started", step_id=step.id, message=f"Step: {step.name}"))
            self._save()

            for attempt in range(task.max_retries + 1):
                if task.id in self._cancelled:
                    step.status = TaskStatus.SKIPPED
                    break

                while task.id in self._paused:
                    await asyncio.sleep(0.5)

                try:
                    step.progress = 10
                    self._save()

                    handler = self._handlers.get(step.agent)
                    if handler:
                        result = await handler(step.params)
                    elif step.agent:
                        result = f"No handler for agent: {step.agent}"
                    else:
                        result = None

                    step.status = TaskStatus.COMPLETED
                    step.progress = 100
                    step.result = result
                    step.completed = time.time()
                    step_results.append({"step": step.name, "status": "completed"})
                    self._emit(task.emit_event("step.completed", step_id=step.id, message=f"Completed: {step.name}"))
                    break

                except asyncio.CancelledError:
                    step.status = TaskStatus.SKIPPED
                    break
                except Exception as e:
                    step.error = str(e)
                    if attempt < task.max_retries:
                        wait = (attempt + 1) * 2
                        log.info("TaskManager: step %s failed (attempt %d/%d), retrying in %ds: %s",
                                 step.name, attempt + 1, task.max_retries, wait, e)
                        self._emit(task.emit_event("step.retry", step_id=step.id,
                                                    message=f"Retry {attempt + 1}/{task.max_retries}: {e}"))
                        await asyncio.sleep(wait)
                    else:
                        step.status = TaskStatus.FAILED
                        step.completed = time.time()
                        step_results.append({"step": step.name, "status": "failed", "error": str(e)})
                        self._emit(task.emit_event("step.failed", step_id=step.id, message=f"Failed: {e}"))

            self._update_task_progress(task)
            self._save()

        all_ok = all(r.get("status") in ("completed", "skipped") for r in step_results)
        task.status = TaskStatus.COMPLETED if all_ok else TaskStatus.FAILED
        task.completed = time.time()
        task.duration_ms = (task.completed - task.started) * 1000
        task.progress = 100
        task.progress_label = "Done" if all_ok else "Failed"
        self._emit(task.emit_event("task.completed" if all_ok else "task.failed",
                                    message=f"Completed: {task.name}" if all_ok else f"Failed: {task.name}"))
        self._save()

        return {
            "task_id": task.id,
            "name": task.name,
            "status": task.status.value,
            "steps": len(task.steps),
            "completed_steps": task.completed_steps(),
            "failed_steps": task.failed_steps(),
            "duration_ms": task.duration_ms,
            "step_results": step_results,
        }

    def _check_dependencies(self, task: Task, step: TaskStep) -> bool:
        if not step.depends_on:
            return True
        step_ids = {s.id for s in task.steps}
        for dep_id in step.depends_on:
            if dep_id not in step_ids:
                return False
            dep_step = next((s for s in task.steps if s.id == dep_id), None)
            if dep_step and dep_step.status != TaskStatus.COMPLETED:
                return False
        return True

    def _update_task_progress(self, task: Task) -> None:
        if not task.steps:
            return
        total = len(task.steps)
        done = task.completed_steps()
        task.progress = int((done / total) * 100)

    # ── Async Run (fire-and-forget with callback) ──

    async def run_task_async(self, task_id: str, callback: Callable[[dict], None] | None = None) -> None:
        result = await self.run_task(task_id)
        if callback:
            try:
                callback(result)
            except Exception:
                pass

    # ── Stats ──

    def get_stats(self) -> dict:
        all_tasks = list(self._tasks.values())
        return {
            "total": len(all_tasks),
            "pending": sum(1 for t in all_tasks if t.status == TaskStatus.PENDING),
            "running": sum(1 for t in all_tasks if t.status == TaskStatus.RUNNING),
            "paused": sum(1 for t in all_tasks if t.status == TaskStatus.PAUSED),
            "completed": sum(1 for t in all_tasks if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in all_tasks if t.status == TaskStatus.FAILED),
            "cancelled": sum(1 for t in all_tasks if t.status == TaskStatus.CANCELLED),
            "active_runs": len(self._active_runs),
        }

    def get_recent_events(self, limit: int = 50) -> list[TaskEvent]:
        events = []
        for task in self._tasks.values():
            events.append(task.emit_event())
        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]
