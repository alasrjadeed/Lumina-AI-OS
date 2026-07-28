from fastapi import APIRouter

from core.tool_framework import tool_framework

router = APIRouter(prefix="/tools", tags=["Tool Framework"])


@router.get("")
async def list_tools():
    return {"tools": tool_framework.list_tools(), "total": len(tool_framework.list_tools())}


@router.post("/{tool_name}/execute")
async def execute_tool(tool_name: str, args: str = "{}"):
    import json as _json
    try:
        kwargs = _json.loads(args)
    except Exception:
        kwargs = {}
    result = tool_framework.execute(tool_name, **kwargs)
    return result


@router.get("/stats")
async def get_stats():
    return tool_framework.get_stats()
