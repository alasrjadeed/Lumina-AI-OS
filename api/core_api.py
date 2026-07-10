"""Core AI API — the unified brain endpoint for all Lumina requests."""

from fastapi import APIRouter, Query
from pydantic import BaseModel

from core.core_ai import core_ai
from core.self_heal_engine import self_healing

router = APIRouter(prefix="/core", tags=["Core AI"])


class ThinkRequest(BaseModel):
    text: str
    context: dict | None = None
    auto_heal: bool = True
    max_retries: int = 3


class VoiceRequest(BaseModel):
    text: str
    reply_by_voice: bool = False


class HealRequest(BaseModel):
    task: str
    test_command: str = ""
    build_command: str = ""
    lint_command: str = ""
    project_dir: str = "."


@router.post("/think")
async def think(req: ThinkRequest):
    """The main entry point: understand → plan → execute → heal → learn → report."""
    return await core_ai.think(req.text, req.context, req.auto_heal, req.max_retries)


@router.post("/code")
async def code_task(
    description: str = Query(""), project_dir: str = Query(""), frameworks: str = Query("")
):
    """Handle a coding task with self-healing enabled."""
    fw_list = [f.strip() for f in frameworks.split(",") if f.strip()] if frameworks else None
    return await core_ai.code_task(description, project_dir, fw_list)


@router.post("/business")
async def business_task(description: str = Query("")):
    return await core_ai.business_task(description)


@router.post("/creative")
async def creative_task(description: str = Query("")):
    return await core_ai.creative_task(description)


@router.post("/voice")
async def voice_pipeline(req: VoiceRequest):
    """Full voice pipeline: speech text → understand → execute → speak reply."""
    return await core_ai.voice_pipeline(req.text, req.reply_by_voice)


@router.get("/status")
async def status():
    return await core_ai.status()


@router.post("/heal")
async def heal(req: HealRequest):
    """Run the self-healing code loop: write → run → fail → analyze → fix → retest."""
    self_healing.project_dir = req.project_dir
    return (
        await self_healing.heal(
            req.task,
            req.test_command,
            req.build_command,
            req.lint_command,
        )
    ).to_dict()


@router.get("/heal/stats")
async def heal_stats():
    return {
        "max_attempts": self_healing.max_attempts,
        "project_dir": self_healing.project_dir,
    }
