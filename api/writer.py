"""AI Content Writer API."""

from fastapi import APIRouter
from pydantic import BaseModel

from core.writer.generator import writer

router = APIRouter(prefix="/writer", tags=["Content Writer"])


class GenerateRequest(BaseModel):
    content_type: str = "blog"
    topic: str = ""
    tone: str = "professional"
    platform: str = "Facebook"
    language: str = "English"
    use_vault: bool = True


@router.get("/types")
async def list_types():
    return {"types": writer.list_types()}


@router.post("/generate")
async def generate(req: GenerateRequest):
    result = await writer.generate(req.content_type, req.topic, req.tone, req.platform, req.language, req.use_vault)
    return result
