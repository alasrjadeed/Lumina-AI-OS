"""Analytics API — cross-module metrics, dashboards, and insights."""

from fastapi import APIRouter, Query
from pydantic import BaseModel

from core.analytics import analytics

router = APIRouter(prefix="/analytics", tags=["Analytics"])


class MetricTrack(BaseModel):
    name: str
    value: float
    unit: str = ""
    category: str = "general"
    tags: dict[str, str] | None = None


@router.post("/track")
async def track_metric(req: MetricTrack):
    analytics.track(req.name, req.value, req.unit, req.category, req.tags)
    analytics._save()
    return {"status": "tracked", "name": req.name, "value": req.value}


@router.get("/metrics")
async def query_metrics(
    name: str = Query(""),
    category: str = Query(""),
    since: float = Query(0),
    limit: int = Query(100),
):
    results = analytics.query(name=name, category=category, since=since, limit=limit)
    return {"metrics": [m.to_dict() for m in results], "total": len(results)}


@router.get("/aggregate/{name}")
async def aggregate(name: str, period: str = Query("day")):
    return analytics.aggregate(name, period=period)


@router.get("/trends/{name}")
async def trends(name: str, buckets: int = Query(24)):
    return {"trends": analytics.trends(name, buckets=buckets)}


@router.get("/forecast/{name}")
async def forecast(name: str, ahead: int = Query(7)):
    return {"forecast": analytics.forecast(name, ahead=ahead)}


@router.get("/dashboard")
async def dashboard():
    return analytics.dashboard()


@router.get("/report")
async def report(categories: str = Query("")):
    cat_list = [c.strip() for c in categories.split(",") if c.strip()] if categories else None
    return {"report": analytics.generate_report(cat_list)}


@router.get("/stats")
async def stats():
    return analytics.stats()


@router.post("/snapshot")
async def snapshot(category: str = Query(""), data: dict | None = None):
    analytics.snapshot(category, data or {})
    return {"status": "saved", "category": category}


@router.get("/snapshot/{category}")
async def get_snapshot(category: str):
    snap = analytics.get_snapshot(category)
    if not snap:
        return {"error": "Snapshot not found"}, 404
    return snap
