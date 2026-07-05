from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from backend.app.services.autonomous.self_healing_loop import SelfHealingLoop
from backend.app.services.autonomous.form_filler import FormFillerService
from backend.app.services.ai.engine import AIEngine

router = APIRouter()
engine = AIEngine()
loop = SelfHealingLoop(engine)
form_filler = FormFillerService(engine)


class PlanRequest(BaseModel):
    goal: str


class ExecuteRequest(BaseModel):
    steps: List[Dict[str, Any]]


class FormFillRequest(BaseModel):
    url: str
    data: Dict[str, Any]
    submit: bool = True


class SocialAccountRequest(BaseModel):
    platform: str
    details: Dict[str, Any]


@router.post("/plan")
async def plan(req: PlanRequest):
    steps = await loop.plan(req.goal)
    return {"goal": req.goal, "steps": [{"name": s.name, "action": s.action, "params": s.params} for s in steps], "count": len(steps)}


@router.post("/execute")
async def execute(req: ExecuteRequest):
    from backend.app.services.ai.agents.base_agent import BaseAgent
    class DynamicExecutor(BaseAgent):
        def __init__(self, ai):
            super().__init__("Executor", "Executor", ai, None)
        async def execute(self, action, params):
            return await self.think(f"Execute action '{action}' with params: {params}")
    executor = DynamicExecutor(engine)
    steps = [type("Step", (), {"name": s.get("name", ""), "action": s.get("action", ""), "params": s.get("params", {}), "status": None, "result": None, "error": None, "retries": 0, "max_retries": 3})() for s in req.steps]
    result = await loop.execute(steps, executor.execute)
    return result


@router.post("/fill-form")
async def fill_form(req: FormFillRequest):
    return await form_filler.fill_form(req.url, req.data, req.submit)


@router.post("/create-account")
async def create_account(req: SocialAccountRequest):
    return await form_filler.create_social_account(req.platform, req.details)


@router.get("/history")
async def get_history():
    return loop.get_history()
