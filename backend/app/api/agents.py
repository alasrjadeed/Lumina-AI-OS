from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List

router = APIRouter()


@router.get("/")
async def list_agents():
    return []


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    raise HTTPException(status_code=404, detail="Agent not found")


@router.post("/{agent_id}/command")
async def agent_command(agent_id: str, command: Dict[str, Any]):
    return {"status": "queued", "agent_id": agent_id}
