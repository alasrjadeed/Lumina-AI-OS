"""Task Manager API — persistent, observable task execution with progress tracking."""

import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.task_manager import TaskPriority, task_manager

router = APIRouter(prefix="/tasks", tags=["Task Manager"])


class StepCreate(BaseModel):
    name: str
    agent: str = ""
    description: str = ""
    params: dict = {}
    depends_on: list[str] = []


class TaskCreate(BaseModel):
    name: str
    description: str = ""
    priority: str = "NORMAL"
    tags: list[str] = []
    max_retries: int = 2
    metadata: dict = {}
    steps: list[StepCreate] = []


class TaskUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    priority: str | None = None
    tags: list[str] | None = None
    metadata: dict | None = None


_priorities = {
    "LOW": TaskPriority.LOW,
    "NORMAL": TaskPriority.NORMAL,
    "HIGH": TaskPriority.HIGH,
    "CRITICAL": TaskPriority.CRITICAL,
}


@router.get("/stats")
async def get_stats():
    return task_manager.get_stats()


@router.get("")
async def list_tasks(
    status: str | None = None, tag: str | None = None, limit: int = 50, offset: int = 0
):
    tasks = task_manager.list_tasks(status=status, tag=tag, limit=limit, offset=offset)
    return {"tasks": [t.to_dict() for t in tasks], "total": len(tasks)}


@router.post("")
async def create_task(req: TaskCreate):
    priority = _priorities.get(req.priority.upper(), TaskPriority.NORMAL)
    task = task_manager.create_task(
        name=req.name,
        description=req.description,
        priority=priority,
        tags=req.tags,
        max_retries=req.max_retries,
        metadata=req.metadata,
    )
    for s in req.steps:
        task_manager.add_step(task.id, s.name, s.agent, s.description, s.params, s.depends_on)
    return task.to_dict()


@router.get("/{task_id}")
async def get_task(task_id: str):
    task = task_manager.get_task(task_id)
    if not task:
        return {"error": "Task not found"}
    return task.to_dict()


@router.patch("/{task_id}")
async def update_task(task_id: str, req: TaskUpdate):
    task = task_manager.get_task(task_id)
    if not task:
        return {"error": "Task not found"}
    if req.name is not None:
        task.name = req.name
    if req.description is not None:
        task.description = req.description
    if req.priority is not None:
        task.priority = _priorities.get(req.priority.upper(), TaskPriority.NORMAL)
    if req.tags is not None:
        task.tags = req.tags
    if req.metadata is not None:
        task.metadata.update(req.metadata)
    return task.to_dict()


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    return {"deleted": task_manager.delete_task(task_id)}


@router.post("/{task_id}/run")
async def run_task(task_id: str):
    result = await task_manager.run_task(task_id)
    return result


@router.post("/{task_id}/pause")
async def pause_task(task_id: str):
    return {"paused": task_manager.pause_task(task_id)}


@router.post("/{task_id}/resume")
async def resume_task(task_id: str):
    return {"resumed": task_manager.resume_task(task_id)}


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str):
    return {"cancelled": task_manager.cancel_task(task_id)}


@router.post("/{task_id}/steps")
async def add_step(task_id: str, req: StepCreate):
    step = task_manager.add_step(
        task_id, req.name, req.agent, req.description, req.params, req.depends_on
    )
    if not step:
        return {"error": "Task not found"}
    return {"id": step.id, "name": step.name}


@router.get("/{task_id}/events")
async def task_events(task_id: str):
    """SSE endpoint for real-time task updates."""

    async def event_stream():
        queue: asyncio.Queue = asyncio.Queue()

        def listener(event):
            queue.put_nowait(event)

        task_manager.on_event(listener)
        try:
            while True:
                event = await queue.get()
                if event.task_id != task_id:
                    continue
                data = json.dumps(
                    {
                        "type": event.type,
                        "status": event.status,
                        "progress": event.progress,
                        "progress_label": event.progress_label,
                        "message": event.message,
                        "timestamp": event.timestamp,
                    }
                )
                yield f"data: {data}\n\n"
                if event.type in ("task.completed", "task.failed", "task.cancelled"):
                    break
        except asyncio.CancelledError:
            pass

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/events/stream")
async def events_stream():
    """Global SSE stream for all task events."""

    async def event_stream():
        queue: asyncio.Queue = asyncio.Queue()

        def listener(event):
            queue.put_nowait(event)

        task_manager.on_event(listener)
        try:
            while True:
                event = await queue.get()
                data = json.dumps(
                    {
                        "type": event.type,
                        "task_id": event.task_id,
                        "status": event.status,
                        "progress": event.progress,
                        "message": event.message,
                        "timestamp": event.timestamp,
                    }
                )
                yield f"data: {data}\n\n"
        except asyncio.CancelledError:
            pass

    return StreamingResponse(event_stream(), media_type="text/event-stream")
