from fastapi import APIRouter

from core.agent_memory import agent_memory_store

router = APIRouter(prefix="/agent-memory", tags=["Agent Memory"])


@router.get("")
async def list_agents():
    return {"agents": agent_memory_store.list_agents()}


@router.get("/{agent_id}")
async def get_agent_memory(agent_id: str):
    return {"agent_id": agent_id, "entries": agent_memory_store.get_memory(agent_id)}


@router.post("/{agent_id}")
async def add_memory(agent_id: str, key: str, value: str, ttl: int | None = None):
    entry = agent_memory_store.add_memory(agent_id, key=key, value=value, ttl=ttl)
    return {"entry": entry}


@router.patch("/{agent_id}/{entry_id}")
async def update_memory(agent_id: str, entry_id: str, value: str):
    entry = agent_memory_store.update_memory(agent_id, entry_id, value=value)
    if not entry:
        return {"error": "Entry not found"}, 404
    return {"entry": entry}


@router.delete("/{agent_id}/{entry_id}")
async def delete_memory(agent_id: str, entry_id: str):
    ok = agent_memory_store.delete_memory(agent_id, entry_id)
    return {"deleted": ok}


@router.post("/{agent_id}/clear")
async def clear_agent(agent_id: str):
    ok = agent_memory_store.clear_agent(agent_id)
    return {"cleared": ok}


@router.get("/stats/all")
async def get_stats():
    return agent_memory_store.get_stats()
