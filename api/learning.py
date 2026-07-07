"""Learning Agent API — remembers patterns, auto-fills, predicts."""

from fastapi import APIRouter
from pydantic import BaseModel

from core.learning.agent import agent

router = APIRouter(prefix="/learning", tags=["Learning"])


class RecordAction(BaseModel):
    action: str
    module: str = ""
    params: dict = {}
    success: bool = True
    duration_ms: float = 0.0


class RememberField(BaseModel):
    form_id: str
    field_name: str
    value: str


class SaveWorkflow(BaseModel):
    name: str
    steps: list[dict]


@router.get("/stats")
async def get_stats():
    return agent.get_stats()


@router.post("/record")
async def record_action(req: RecordAction):
    agent.record(req.action, req.module, req.params, req.success, req.duration_ms)
    return {"status": "ok"}


@router.get("/patterns")
async def get_patterns():
    return {"patterns": [{"sequence": p.sequence, "frequency": p.frequency}
                        for p in agent.get_frequent_patterns(10)]}


@router.get("/suggest/{action}")
async def suggest_next(action: str):
    next_action = agent.suggest_next_action([action])
    return {"next": next_action}


@router.post("/remember")
async def remember_field(req: RememberField):
    agent.remember_field(req.form_id, req.field_name, req.value)
    return {"status": "ok"}


@router.get("/fields/{form_id}")
async def get_fields(form_id: str):
    return {"fields": agent.suggest_fields(form_id)}


@router.get("/workflows")
async def list_workflows():
    return {"workflows": agent.list_workflows()}


@router.post("/workflows")
async def save_workflow(req: SaveWorkflow):
    agent.save_workflow(req.name, req.steps)
    return {"status": "ok"}


@router.post("/workflows/{name}/run")
async def run_workflow(name: str):
    return agent.run_workflow(name)
