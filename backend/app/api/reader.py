from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.app.services.reader.reader_service import ReaderService, ReaderCommand
from backend.app.services.ai.engine import AIEngine

router = APIRouter()
engine = AIEngine()
reader_service = ReaderService(engine)


class ReadRequest(BaseModel):
    path: Optional[str] = None
    text: Optional[str] = None


class ReaderCommandRequest(BaseModel):
    command: str
    page: Optional[int] = None


@router.post("/read")
async def read(req: ReadRequest):
    if req.path:
        return await reader_service.read_file(req.path)
    if req.text:
        return await reader_service.read_text(req.text)
    raise HTTPException(status_code=400, detail="Provide path or text")


@router.post("/command")
async def reader_command(req: ReaderCommandRequest):
    cmd = ReaderCommand(req.command) if req.command in ("read", "pause", "continue", "faster", "slower", "repeat", "goto_page") else ReaderCommand.READ
    return await reader_service.command(cmd, page=req.page)
