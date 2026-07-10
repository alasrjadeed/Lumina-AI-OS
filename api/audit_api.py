"""Audit Trail API — query, filter, and report on every agent action."""

from fastapi import APIRouter, Query

from core.audit import AuditAction, audit_trail

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/entries")
async def query(
    agent: str = Query(""),
    action: str = Query(""),
    status: str = Query(""),
    since: float = Query(0),
    limit: int = Query(100),
):
    return {
        "entries": [
            e.to_dict()
            for e in audit_trail.query(
                agent=agent,
                action=action,
                status=status,
                since=since,
                limit=limit,
            )
        ],
    }


@router.get("/today")
async def today_summary():
    return audit_trail.get_today_summary()


@router.get("/report")
async def report(date: str = Query("")):
    return {"report": audit_trail.get_daily_report(date)}


@router.get("/stats")
async def stats():
    return audit_trail.get_stats()


@router.get("/actions")
async def list_actions():
    return {"actions": [a.value for a in AuditAction]}
