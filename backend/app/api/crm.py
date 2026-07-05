from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from backend.app.services.memory.memory_manager import MemoryManager
from backend.app.services.crm.lead_manager import LeadManager
from backend.app.services.crm.sales_pipeline import SalesPipeline
from backend.app.services.crm.proposal_generator import ProposalGenerator
from backend.app.services.crm.quotation_generator import QuotationGenerator
from backend.app.services.crm.followup_manager import FollowUpManager
from backend.app.services.crm.calendar_service import CalendarService
from backend.app.services.crm.client_workspace import ClientWorkspace
from backend.app.services.ai.engine import AIEngine

router = APIRouter()
memory = MemoryManager()
ai = AIEngine()
lead_manager = LeadManager(memory)
pipeline = SalesPipeline(memory)
proposal_gen = ProposalGenerator(ai)
quotation_gen = QuotationGenerator(ai)
followups = FollowUpManager(memory)
calendar = CalendarService(memory)
workspaces = ClientWorkspace(memory)


class LeadCreate(BaseModel):
    company_name: str
    contact_person: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    website: Optional[str] = ""
    industry: Optional[str] = ""
    notes: Optional[str] = ""


class ProposalRequest(BaseModel):
    client: str
    scope: str
    pricing: str
    timeline: str


class QuotationRequest(BaseModel):
    client: str
    items: List[Dict[str, Any]]
    tax: float = 0.0
    discount: float = 0.0


class EventCreate(BaseModel):
    title: str
    start: str
    end: str
    event_type: str = "meeting"
    description: str = ""


class FollowUpSchedule(BaseModel):
    lead_id: str
    days: int = 5
    note: str = ""


class WorkspaceNote(BaseModel):
    company: str
    note: str


class WorkspaceTask(BaseModel):
    company: str
    task: str


# Lead Management
@router.post("/leads")
async def create_lead(req: LeadCreate):
    return await lead_manager.create_lead(req.model_dump())


@router.get("/leads")
async def list_leads(status: Optional[str] = None):
    return await lead_manager.list_leads(status)


@router.get("/leads/{lead_id}")
async def get_lead(lead_id: str):
    lead = await lead_manager.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.put("/leads/{lead_id}/qualify")
async def qualify_lead(lead_id: str):
    return await lead_manager.qualify_lead(lead_id)


@router.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str):
    return {"deleted": await lead_manager.delete_lead(lead_id)}


# Pipeline
@router.put("/pipeline/{lead_id}/move")
async def move_pipeline(lead_id: str, to_stage: str = Query(...)):
    return await pipeline.move_stage(lead_id, to_stage)


@router.get("/pipeline")
async def get_pipeline():
    return await pipeline.get_pipeline()


# Proposals & Quotations
@router.post("/proposals")
async def create_proposal(req: ProposalRequest):
    return await proposal_gen.generate(req.client, req.scope, req.pricing, req.timeline)


@router.post("/quotations")
async def create_quotation(req: QuotationRequest):
    return await quotation_gen.create_quotation(req.client, req.items, req.tax, req.discount)


# Follow-ups
@router.post("/followups")
async def schedule_followup(req: FollowUpSchedule):
    return await followups.schedule(req.lead_id, req.days, req.note)


@router.get("/followups/pending")
async def pending_followups():
    return await followups.get_pending()


# Calendar
@router.post("/calendar")
async def create_event(req: EventCreate):
    return await calendar.create_event(req.title, req.start, req.end, req.event_type, req.description)


@router.get("/calendar")
async def list_events(date_from: Optional[str] = None, date_to: Optional[str] = None):
    return await calendar.list_events(date_from, date_to)


# Client Workspaces
@router.post("/workspaces/{company}")
async def create_workspace(company: str, contact: Dict[str, Any]):
    return await workspaces.create_workspace(company, contact)


@router.get("/workspaces/{company}")
async def get_workspace(company: str):
    ws = await workspaces.get_workspace(company)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return ws


@router.post("/workspaces/{company}/notes")
async def add_note(company: str, req: WorkspaceNote):
    return await workspaces.add_note(company, req.note)


@router.post("/workspaces/{company}/tasks")
async def add_task(company: str, req: WorkspaceTask):
    return await workspaces.add_task(company, req.task)
