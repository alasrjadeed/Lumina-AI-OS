"""AI Assistant API — voice & text command execution."""

from fastapi import APIRouter
from pydantic import BaseModel

from core.assistant.agent import assistant

router = APIRouter(prefix="/assistant", tags=["Assistant"])


class CommandRequest(BaseModel):
    command: str
    voice: bool = False


@router.post("/process")
async def process_command(req: CommandRequest):
    result = await assistant.process(req.command)
    return result


@router.get("/capabilities")
async def get_capabilities():
    from core.assistant.agent import CAPABILITIES
    return {"capabilities": CAPABILITIES}
