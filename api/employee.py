"""Autonomous Employee API v2 — mission management, streaming, memory, and tools."""

import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.employee.orchestrator import TOOLS, employee, load_memory

router = APIRouter(prefix="/employee", tags=["Employee"])


class GoalRequest(BaseModel):
    goal: str
    headless: bool = True


class MemoryRequest(BaseModel):
    key: str = ""
    value: str = ""
    action: str = "get"


@router.post("/execute")
async def execute_goal(req: GoalRequest):
    result = await employee.execute(req.goal)
    return result


@router.post("/execute/stream")
async def execute_goal_stream(req: GoalRequest):
    """Execute a goal with real-time SSE streaming of progress."""

    async def event_stream():
        queue: asyncio.Queue = asyncio.Queue()

        async def on_progress(data: dict):
            await queue.put(data)

        employee.on_progress(on_progress)

        execute_task = asyncio.create_task(employee.execute(req.goal))

        while True:
            try:
                data = await asyncio.wait_for(queue.get(), timeout=1.0)
                yield f"data: {json.dumps(data)}\n\n"
            except TimeoutError:
                if execute_task.done():
                    break
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

        result = execute_task.result()
        yield f"data: {json.dumps({'type': 'final', 'result': result})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/history")
async def get_history(limit: int = 10):
    return {"missions": employee.get_history(limit=limit)}


@router.post("/memory")
async def manage_memory(req: MemoryRequest):
    memory = load_memory()
    if req.action == "get":
        if req.key:
            return {"key": req.key, "value": memory.get("knowledge", {}).get(req.key, "Not found")}
        return memory
    elif req.action == "set":
        memory.setdefault("knowledge", {})[req.key] = req.value
        from core.employee.orchestrator import save_memory

        save_memory(memory)
        return {"status": "ok", "key": req.key}
    elif req.action == "set_context":
        memory.setdefault("contexts", {})["current"] = req.value
        from core.employee.orchestrator import save_memory

        save_memory(memory)
        return {"status": "ok", "context": req.value[:100]}
    elif req.action == "clear":
        from core.employee.orchestrator import save_memory

        save_memory({"missions": [], "knowledge": {}, "preferences": {}, "contexts": {}})
        return {"status": "cleared"}
    return {"status": "error", "error": "Unknown action"}


@router.get("/tools")
async def list_tools():
    return {"tools": list(TOOLS.values())}


@router.get("/status")
async def employee_status():
    memory = load_memory()
    return {
        "status": "ready",
        "tools_available": len(TOOLS),
        "missions_completed": len(memory.get("missions", [])),
        "facts_known": len(memory.get("knowledge", {})),
    }
