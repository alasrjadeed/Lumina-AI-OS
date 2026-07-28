from fastapi import APIRouter, Body

from core.brain import brain

router = APIRouter(prefix="/brain", tags=["brain"])


@router.post("/think")
async def think():
    thought = await brain.think()
    return thought.to_dict()


@router.post("/think-and-command")
async def think_and_command():
    thought = await brain.think_and_command()
    return thought.to_dict()


@router.post("/command")
async def execute_command(cmd: dict):
    result = await brain.command(cmd)
    return {"result": result}


@router.get("/observe")
async def observe():
    snapshot = await brain.observe()
    return snapshot


@router.get("/status")
async def status():
    return brain.status


@router.get("/history")
async def history():
    return brain.history


@router.post("/start")
async def start():
    if not brain._running:
        import asyncio
        brain._task = asyncio.create_task(brain.loop())
    return {"status": "started", "running": brain._running}


@router.post("/stop")
async def stop():
    brain.stop()
    return {"status": "stopped"}


@router.post("/interval")
async def set_interval(interval: int = Body(..., embed=True)):
    brain.thinking_interval = max(10, min(interval, 3600))
    return {"interval": brain.thinking_interval}
