from fastapi import APIRouter, HTTPException

from core.agent_builder import BUILTIN_TOOLS, blueprint_store

router = APIRouter(prefix="/agent-blueprints", tags=["Agent Builder"])


@router.get("/tools")
async def list_available_tools():
    return {"tools": BUILTIN_TOOLS}


@router.get("")
async def list_blueprints():
    return {"blueprints": [b.to_dict() for b in blueprint_store.list()]}


@router.post("")
async def create_blueprint(name: str, description: str = "", system_prompt: str = "", tools: str = "", model: str = "gpt-4o-mini", temperature: float = 0.7, max_tokens: int = 2048):
    tool_list = [t.strip() for t in tools.split(",") if t.strip()] if tools else []
    bp = blueprint_store.create(name=name, description=description, system_prompt=system_prompt, tools=tool_list, model=model, temperature=temperature, max_tokens=max_tokens)
    return {"blueprint": bp.to_dict()}


@router.get("/{blueprint_id}")
async def get_blueprint(blueprint_id: str):
    bp = blueprint_store.get(blueprint_id)
    if not bp:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    return {"blueprint": bp.to_dict()}


@router.patch("/{blueprint_id}")
async def update_blueprint(blueprint_id: str, name: str | None = None, description: str | None = None, system_prompt: str | None = None, tools: str | None = None, model: str | None = None, temperature: float | None = None, max_tokens: int | None = None):
    kwargs = {}
    if name is not None:
        kwargs["name"] = name
    if description is not None:
        kwargs["description"] = description
    if system_prompt is not None:
        kwargs["system_prompt"] = system_prompt
    if tools is not None:
        kwargs["tools"] = [t.strip() for t in tools.split(",") if t.strip()]
    if model is not None:
        kwargs["model"] = model
    if temperature is not None:
        kwargs["temperature"] = temperature
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    bp = blueprint_store.update(blueprint_id, **kwargs)
    if not bp:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    return {"blueprint": bp.to_dict()}


@router.post("/{blueprint_id}/duplicate")
async def duplicate_blueprint(blueprint_id: str):
    bp = blueprint_store.duplicate(blueprint_id)
    if not bp:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    return {"blueprint": bp.to_dict()}


@router.delete("/{blueprint_id}")
async def delete_blueprint(blueprint_id: str):
    ok = blueprint_store.delete(blueprint_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    return {"deleted": True}


@router.get("/stats/all")
async def get_stats():
    return blueprint_store.get_stats()
