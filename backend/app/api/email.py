from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from backend.app.services.email.email_service import EmailService
from backend.app.services.ai.engine import AIEngine
from backend.app.services.memory.memory_manager import MemoryManager

router = APIRouter()
engine = AIEngine()
memory = MemoryManager()
email_service = EmailService(engine, memory)


class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    html: Optional[str] = None


class ConfigureRequest(BaseModel):
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_pass: str


class DraftRequest(BaseModel):
    prompt: str
    tone: str = "professional"


@router.post("/configure")
async def configure(req: ConfigureRequest):
    email_service.configure(req.smtp_host, req.smtp_port, req.smtp_user, req.smtp_pass)
    return {"status": "configured"}


@router.post("/send")
async def send_email(req: SendEmailRequest):
    return await email_service.send_email(req.to, req.subject, req.body, req.html)


@router.post("/draft")
async def draft_email(req: DraftRequest):
    return await email_service.draft_email(req.prompt, req.tone)


@router.get("/threads")
async def list_threads():
    return await email_service.list_threads()


@router.get("/threads/{thread_id}")
async def get_thread(thread_id: str):
    thread = await email_service.track_reply(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread
