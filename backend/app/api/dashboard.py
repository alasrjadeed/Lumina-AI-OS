from fastapi import APIRouter
from typing import Any, Dict

router = APIRouter()


@router.get("/")
async def dashboard():
    return {
        "status": "running",
        "agents_active": 0,
        "tasks_pending": 0,
        "tasks_completed_today": 0,
        "memory_usage": "0 MB",
        "uptime": "0h 0m",
    }


@router.get("/stats")
async def stats():
    return {
        "total_tasks": 0,
        "completed_tasks": 0,
        "failed_tasks": 0,
        "active_agents": 0,
    }
