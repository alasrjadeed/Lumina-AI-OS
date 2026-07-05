from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from backend.app.services.ai.engine import AIEngine
from backend.app.services.memory.memory_manager import MemoryManager
from backend.app.services.crm.lead_generation import LeadGenerationService

router = APIRouter()
engine = AIEngine()
memory = MemoryManager()
lead_gen = LeadGenerationService(engine, memory)


class SearchRequest(BaseModel):
    criteria: str
    location: str = ""


class EnrichRequest(BaseModel):
    company_name: str
    website: str = ""


@router.post("/search")
async def search_businesses(req: SearchRequest):
    return await lead_gen.search_businesses(req.criteria, req.location)


@router.post("/enrich")
async def enrich_lead(req: EnrichRequest):
    return await lead_gen.enrich_lead(req.company_name, req.website)


@router.get("/stored")
async def get_stored():
    return await lead_gen.get_stored_leads()
