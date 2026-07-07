"""Advanced Automation API — workflow builder, execution engine, triggers, and history."""

from fastapi import APIRouter
from pydantic import BaseModel

from core.automation.engine import (
    engine, WorkflowModel, StepModel, TriggerConfig,
    TRIGGER_TYPES, ACTION_TYPES,
)

router = APIRouter(prefix="/automation", tags=["Automation"])


# ── Schemas ──

class WorkflowCreate(BaseModel):
    name: str
    description: str = ""
    trigger: dict = {}
    steps: list[dict] = []
    tags: list[str] = []


class WorkflowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    trigger: dict | None = None
    steps: list[dict] | None = None
    tags: list[str] | None = None
    enabled: bool | None = None


class WebhookBody(BaseModel):
    body: dict | None = None


# ── Endpoints ──

@router.get("/workflows")
async def list_workflows():
    workflows = engine.list_workflows()
    return {
        "workflows": [w.to_dict() for w in workflows],
        "total": len(workflows),
    }


@router.post("/workflows")
async def create_workflow(req: WorkflowCreate):
    trigger = TriggerConfig.from_dict(req.trigger) if req.trigger else None
    steps = [StepModel.from_dict(s) for s in req.steps] if req.steps else []
    wf = engine.create_workflow(
        name=req.name, description=req.description,
        trigger=trigger, steps=steps, tags=req.tags,
    )
    return {"workflow": wf.to_dict()}


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    wf = engine.get_workflow(workflow_id)
    if not wf:
        return {"error": "Workflow not found"}, 404
    return {"workflow": wf.to_dict()}


@router.put("/workflows/{workflow_id}")
async def update_workflow(workflow_id: str, req: WorkflowUpdate):
    data = req.model_dump(exclude_unset=True)
    wf = engine.update_workflow(workflow_id, data)
    if not wf:
        return {"error": "Workflow not found"}, 404
    return {"workflow": wf.to_dict()}


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    ok = engine.delete_workflow(workflow_id)
    if not ok:
        return {"error": "Workflow not found"}, 404
    return {"status": "deleted"}


@router.post("/workflows/{workflow_id}/toggle")
async def toggle_workflow(workflow_id: str):
    wf = engine.toggle_workflow(workflow_id)
    if not wf:
        return {"error": "Workflow not found"}, 404
    return {"workflow": wf.to_dict()}


@router.post("/workflows/{workflow_id}/run")
async def run_workflow(workflow_id: str):
    wf = engine.get_workflow(workflow_id)
    if not wf:
        return {"error": "Workflow not found"}, 404
    if not wf.enabled:
        return {"error": "Workflow is disabled"}, 400
    run_id = await engine.execute(workflow_id)
    return {"status": "started", "run_id": run_id}


@router.get("/workflows/{workflow_id}/history")
async def workflow_history(workflow_id: str, limit: int = 20):
    records = engine.get_history(workflow_id=workflow_id, limit=limit)
    return {"history": [r.to_dict() for r in records], "total": len(records)}


@router.get("/history")
async def all_history(limit: int = 50):
    records = engine.get_history(limit=limit)
    return {"history": [r.to_dict() for r in records], "total": len(records)}


@router.get("/history/{run_id}")
async def get_run(run_id: str):
    run = engine.get_run(run_id)
    if not run:
        return {"error": "Run not found"}, 404
    return {"run": run.to_dict()}


@router.get("/triggers")
async def list_triggers():
    return {"triggers": TRIGGER_TYPES}


@router.get("/actions")
async def list_actions():
    return {"actions": ACTION_TYPES}


@router.post("/triggers/webhook/{token}")
async def webhook_trigger(token: str, req: WebhookBody = WebhookBody()):
    result = await engine.handle_webhook(token, req.body)
    return result
