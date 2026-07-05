from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.app.services.explain.explain_service import ExplainService, ExplainLevel
from backend.app.services.ai.engine import AIEngine

router = APIRouter()
engine = AIEngine()
explain_service = ExplainService(engine)


class ExplainRequest(BaseModel):
    topic: str = ""
    code: Optional[str] = None
    language: Optional[str] = ""
    content: Optional[str] = None
    filename: Optional[str] = ""
    url: Optional[str] = None
    page_content: Optional[str] = None
    report_type: Optional[str] = None
    report_data: Optional[str] = None
    level: str = "intermediate"


@router.post("/text")
async def explain_text(req: ExplainRequest):
    level = ExplainLevel(req.level) if req.level in ("beginner", "intermediate", "expert") else ExplainLevel.INTERMEDIATE
    return await explain_service.explain_text(req.topic, level)


@router.post("/code")
async def explain_code(req: ExplainRequest):
    if not req.code:
        raise HTTPException(status_code=400, detail="code field required")
    level = ExplainLevel(req.level) if req.level in ("beginner", "intermediate", "expert") else ExplainLevel.INTERMEDIATE
    return await explain_service.explain_code(req.code, req.language or "", level)


@router.post("/document")
async def explain_document(req: ExplainRequest):
    if not req.content:
        raise HTTPException(status_code=400, detail="content field required")
    level = ExplainLevel(req.level) if req.level in ("beginner", "intermediate", "expert") else ExplainLevel.INTERMEDIATE
    return await explain_service.explain_document(req.content, req.filename or "", level)


@router.post("/website")
async def explain_website(req: ExplainRequest):
    if not req.url or not req.page_content:
        raise HTTPException(status_code=400, detail="url and page_content required")
    level = ExplainLevel(req.level) if req.level in ("beginner", "intermediate", "expert") else ExplainLevel.INTERMEDIATE
    return await explain_service.explain_website(req.url, req.page_content, level)


@router.post("/report")
async def explain_report(req: ExplainRequest):
    if not req.report_type or not req.report_data:
        raise HTTPException(status_code=400, detail="report_type and report_data required")
    level = ExplainLevel(req.level) if req.level in ("beginner", "intermediate", "expert") else ExplainLevel.INTERMEDIATE
    return await explain_service.explain_report(req.report_type, req.report_data, level)
