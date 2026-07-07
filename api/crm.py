from fastapi import APIRouter
from pydantic import BaseModel

from core.crm.pipeline import DealStage, crm

router = APIRouter(prefix="/crm", tags=["CRM"])


class ContactCreate(BaseModel):
    name: str
    email: str = ""
    phone: str = ""
    company: str = ""
    source: str = "manual"
    tags: list[str] = []


class DealCreate(BaseModel):
    title: str
    value: float
    contact_id: str
    stage: str = "lead"


class DealStageUpdate(BaseModel):
    deal_id: str
    stage: str


class ActivityCreate(BaseModel):
    contact_id: str
    type: str
    description: str


@router.get("/contacts")
async def list_contacts(search: str = ""):
    return {"contacts": crm.list_contacts(search)}


@router.post("/contacts")
async def add_contact(req: ContactCreate):
    contact = crm.add_contact(
        req.name, req.email, req.phone, req.company,
        source=req.source, tags=req.tags,
    )
    return contact


@router.get("/deals")
async def list_deals(stage: str | None = None):
    return {"deals": crm.list_deals(stage)}


@router.post("/deals")
async def add_deal(req: DealCreate):
    stage = DealStage(req.stage) if req.stage in [s.value for s in DealStage] else DealStage.LEAD
    deal = crm.add_deal(req.title, req.value, req.contact_id, stage)
    return deal


@router.post("/deals/stage")
async def update_stage(req: DealStageUpdate):
    try:
        stage = DealStage(req.stage)
    except ValueError:
        return {"error": f"Invalid stage. Valid: {[s.value for s in DealStage]}"}
    deal = crm.update_deal_stage(req.deal_id, stage)
    return deal or {"error": "Deal not found"}


@router.get("/summary")
async def sales_summary():
    return crm.get_sales_summary()


@router.post("/activities")
async def add_activity(req: ActivityCreate):
    return crm.add_activity(req.contact_id, req.type, req.description)
