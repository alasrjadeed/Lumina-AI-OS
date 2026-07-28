from fastapi import APIRouter, Query

from core.memory_tree import build_tree, get_branch, search_memory

router = APIRouter(prefix="/memory-tree", tags=["Memory Tree"])


@router.get("")
async def get_memory_tree():
    tree = build_tree()
    return {"tree": tree}


@router.get("/branch/{layer}")
async def get_memory_branch(layer: str):
    items = get_branch(layer)
    return {"layer": layer, "items": items, "count": len(items)}


@router.get("/search")
async def search(q: str = Query("", min_length=1)):
    results = search_memory(q)
    return {"query": q, "results": results, "count": len(results)}
