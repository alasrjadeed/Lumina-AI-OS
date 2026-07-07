"""Marketing automation API routes."""

from fastapi import APIRouter
from pydantic import BaseModel

from core.plugins.marketing import (
    complete_campaign,
    create_campaign,
    get_campaign,
    get_campaign_metrics,
    get_content_calendar,
    get_summary,
    launch_campaign,
    list_campaigns,
    pause_campaign,
    publish_content,
    schedule_content,
    track_click,
    track_conversion,
    track_impression,
)

router = APIRouter(prefix="/marketing", tags=["Marketing"])


class CampaignCreate(BaseModel):
    name: str
    channel: str = "email"
    budget: float = 0.0


class ContentCreate(BaseModel):
    title: str
    content: str
    channel: str = "web"
    tags: list[str] = []


class TrackRequest(BaseModel):
    name: str
    count: int = 1


@router.get("/campaigns")
async def campaigns(status: str = ""):
    return {"campaigns": [{"name": c.name, "channel": c.channel.value,
                           "budget": c.budget, "spent": c.spent,
                           "impressions": c.impressions, "clicks": c.clicks,
                           "conversions": c.conversions, "status": c.status}
                          for c in list_campaigns(status)]}


@router.post("/campaigns")
async def create(req: CampaignCreate):
    c = create_campaign(req.name, req.channel, req.budget)
    return {"name": c.name, "channel": c.channel.value, "budget": c.budget, "status": c.status}


@router.get("/campaigns/{name}")
async def get(name: str):
    c = get_campaign(name)
    if not c:
        return {"error": "Campaign not found"}
    return {"name": c.name, "channel": c.channel.value, "budget": c.budget,
            "spent": c.spent, "impressions": c.impressions, "clicks": c.clicks,
            "conversions": c.conversions, "status": c.status}


@router.post("/campaigns/{name}/launch")
async def launch(name: str):
    ok = launch_campaign(name)
    return {"success": ok, "status": "active" if ok else "error"}


@router.post("/campaigns/{name}/pause")
async def pause(name: str):
    ok = pause_campaign(name)
    return {"success": ok, "status": "paused" if ok else "error"}


@router.post("/campaigns/{name}/complete")
async def complete(name: str):
    ok = complete_campaign(name)
    return {"success": ok}


@router.get("/campaigns/{name}/metrics")
async def metrics(name: str):
    return get_campaign_metrics(name)


@router.post("/campaigns/{name}/impressions")
async def impression(req: TrackRequest):
    track_impression(req.name, req.count)
    return {"status": "ok"}


@router.post("/campaigns/{name}/clicks")
async def click(req: TrackRequest):
    track_click(req.name, req.count)
    return {"status": "ok"}


@router.post("/campaigns/{name}/conversions")
async def conversion(req: TrackRequest):
    track_conversion(req.name, req.count)
    return {"status": "ok"}


@router.get("/content")
async def content(status: str = "", channel: str = ""):
    items = get_content_calendar(status, channel)
    return {"items": [{"title": c.title, "channel": c.channel,
                       "status": c.status, "tags": c.tags} for c in items]}


@router.post("/content")
async def create_content(req: ContentCreate):
    item = schedule_content(req.title, req.content, req.channel, tags=req.tags)
    return {"title": item.title, "channel": item.channel, "status": item.status}


@router.post("/content/{title}/publish")
async def publish(title: str):
    ok = publish_content(title)
    return {"success": ok}


@router.get("/summary")
async def summary():
    return get_summary()
