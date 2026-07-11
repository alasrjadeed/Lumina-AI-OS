"""Agent Presets API — pre-configured agent profiles."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.presets.registry import AgentPreset, registry

router = APIRouter(prefix="/presets", tags=["Presets"])


class CreatePresetRequest(BaseModel):
    name: str
    label: str
    description: str
    system_prompt: str = ""
    tools: list[str] = []
    category: str = "general"
    tags: list[str] = []


@router.get("", summary="List all agent presets")
async def list_presets(category: str | None = None):
    return {"presets": [p.to_dict() for p in registry.list(category=category)], "categories": registry.categories()}


@router.get("/{name}", summary="Get a specific preset")
async def get_preset(name: str):
    preset = registry.get(name)
    if not preset:
        raise HTTPException(404, f"Preset '{name}' not found")
    return preset.to_dict()


@router.post("", summary="Create a custom preset")
async def create_preset(req: CreatePresetRequest):
    preset = AgentPreset(
        name=req.name,
        label=req.label,
        description=req.description,
        system_prompt=req.system_prompt,
        tools=req.tools,
        category=req.category,
        tags=req.tags,
    )
    registry.register(preset)
    return {"status": "ok", "preset": preset.to_dict()}
