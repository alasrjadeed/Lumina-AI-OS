from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

router = APIRouter()


class MemoryEntry(BaseModel):
    key: str
    value: Any
    namespace: str = "default"


@router.post("/")
async def store_memory(entry: MemoryEntry):
    return {"status": "stored", "key": entry.key}


@router.get("/{key}")
async def get_memory(key: str, namespace: str = "default"):
    raise HTTPException(status_code=404, detail="Memory not found")


@router.delete("/{key}")
async def delete_memory(key: str, namespace: str = "default"):
    return {"status": "deleted"}


@router.get("/")
async def list_memories(namespace: str = "default"):
    return []
