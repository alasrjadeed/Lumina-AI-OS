from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from backend.app.services.whatsapp.whatsapp_service import WhatsAppService
from backend.app.services.ai.engine import AIEngine
from backend.app.services.memory.memory_manager import MemoryManager

router = APIRouter()
engine = AIEngine()
memory = MemoryManager()
whatsapp = WhatsAppService(engine, memory)


class SendMessageRequest(BaseModel):
    to: str
    message: str
    template: Optional[str] = None


class ConfigureRequest(BaseModel):
    api_key: str
    phone_number_id: str


class CatalogRequest(BaseModel):
    action: str
    product: Optional[Dict[str, Any]] = {}


class ReplyRequest(BaseModel):
    message: str
    context: Optional[str] = None


@router.post("/configure")
async def configure(req: ConfigureRequest):
    whatsapp.configure(req.api_key, req.phone_number_id)
    return {"status": "configured"}


@router.post("/send")
async def send_message(req: SendMessageRequest):
    return await whatsapp.send_message(req.to, req.message, req.template)


@router.post("/reply")
async def generate_reply(req: ReplyRequest):
    reply = await whatsapp.generate_reply(req.message, req.context)
    return {"reply": reply}


@router.get("/conversations")
async def conversations(contact: Optional[str] = None):
    return await whatsapp.get_conversations(contact)


@router.post("/catalog")
async def manage_catalog(req: CatalogRequest):
    return await whatsapp.manage_catalog(req.action, req.product)
