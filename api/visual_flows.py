"""Visual Agent Flows API — drag-and-drop multi-agent workflow builder."""

from fastapi import APIRouter, Query
from pydantic import BaseModel

from core.visual_flows import flow_manager, VisualFlow

router = APIRouter(prefix="/visual-flows", tags=["Visual Flows"])


class CreateFlow(BaseModel):
    name: str
    description: str = ""
    nodes: list[dict] = []
    edges: list[dict] = []


class UpdateFlow(BaseModel):
    flow_id: str
    name: str = ""
    description: str = ""
    nodes: list[dict] | None = None
    edges: list[dict] | None = None


class ExecuteFlow(BaseModel):
    flow_id: str
    input_text: str = ""


@router.get("/palette")
async def get_palette():
    return {"palette": flow_manager.get_palette()}


@router.get("")
async def list_flows():
    return {"flows": [f.to_dict() for f in flow_manager.list()], "total": len(flow_manager.list())}


@router.get("/{flow_id}")
async def get_flow(flow_id: str):
    flow = flow_manager.get(flow_id)
    if not flow:
        return {"error": "Flow not found"}, 404
    return {"flow": flow.to_dict()}


@router.post("/create")
async def create_flow(req: CreateFlow):
    flow = flow_manager.create(req.name, req.description, req.nodes, req.edges)
    return {"status": "created", "flow": flow.to_dict()}


@router.put("/update")
async def update_flow(req: UpdateFlow):
    kwargs = {}
    if req.name: kwargs["name"] = req.name
    if req.description: kwargs["description"] = req.description
    if req.nodes is not None: kwargs["nodes"] = req.nodes
    if req.edges is not None: kwargs["edges"] = req.edges

    flow = flow_manager.update(req.flow_id, **kwargs)
    if not flow:
        return {"error": "Flow not found"}, 404
    return {"status": "updated", "flow": flow.to_dict()}


@router.delete("/{flow_id}")
async def delete_flow(flow_id: str):
    ok = flow_manager.delete(flow_id)
    return {"status": "deleted" if ok else "not_found"}


@router.post("/execute")
async def execute_flow(req: ExecuteFlow):
    return await flow_manager.execute(req.flow_id, req.input_text)


@router.get("/stats")
async def stats():
    return flow_manager.stats()
