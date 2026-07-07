"""Task Queue API — chain and execute multi-step pipelines."""

from fastapi import APIRouter
from pydantic import BaseModel

from core.queue.engine import queue

router = APIRouter(prefix="/queue", tags=["Task Queue"])


class TaskCreate(BaseModel):
    name: str
    action: str = "Generate content"
    module: str = "content"
    params: dict = {}
    depends_on: list[str] = []


class PipelineCreate(BaseModel):
    name: str
    tasks: list[TaskCreate] = []


@router.get("/stats")
async def get_stats():
    return queue.get_stats()


@router.get("/pipelines")
async def list_pipelines():
    return {"pipelines": [{"id": p.id, "name": p.name, "status": p.status,
                           "tasks": len(p.tasks), "created": p.created}
                          for p in queue.list_pipelines()]}


@router.post("/pipelines")
async def create_pipeline(req: PipelineCreate):
    p = queue.create_pipeline(req.name)
    for t in req.tasks:
        queue.add_task(p.id, t.name, t.action, t.module, t.params, t.depends_on)
    return {"id": p.id, "name": p.name, "tasks": len(req.tasks)}


@router.get("/pipelines/{pipeline_id}")
async def get_pipeline(pipeline_id: str):
    p = queue.get_pipeline(pipeline_id)
    if not p:
        return {"error": "Not found"}
    return {"id": p.id, "name": p.name, "status": p.status,
            "tasks": [{"id": t.id, "name": t.name, "action": t.action, "module": t.module,
                       "status": t.status.value, "error": t.error[:100],
                       "duration_ms": t.duration_ms, "retries": t.retries}
                      for t in p.tasks]}


@router.delete("/pipelines/{pipeline_id}")
async def delete_pipeline(pipeline_id: str):
    return {"deleted": queue.delete_pipeline(pipeline_id)}


@router.post("/pipelines/{pipeline_id}/run")
async def run_pipeline(pipeline_id: str):
    return await queue.run_pipeline(pipeline_id)


@router.post("/pipelines/{pipeline_id}/tasks")
async def add_task(pipeline_id: str, req: TaskCreate):
    task = queue.add_task(pipeline_id, req.name, req.action, req.module, req.params, req.depends_on)
    if not task:
        return {"error": "Pipeline not found"}
    return {"id": task.id, "name": task.name}


@router.post("/run-all")
async def run_all():
    return await queue.run_all_pending()
