"""Multi-Agent System API — CEO orchestration, specialist agents, and workflow management."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.agents.runner import runner, AGENT_METADATA
from core.agents.approval import approval_gate, ApprovalLevel
from core.agents.languages import language_engine
from core.agents.learning import learning_engine
from core.agents.routine import autonomous_routine
from core.agents.employee import employee

router = APIRouter(prefix="/multiagent", tags=["Multi-Agent"])


class OrchestrateRequest(BaseModel):
    task: str
    context: dict | None = None


class AgentTask(BaseModel):
    agent: str
    task: str
    context: dict | None = None
    model: str = ""


class BatchTask(BaseModel):
    tasks: list[AgentTask]


class ApprovalAction(BaseModel):
    request_id: str
    note: str = ""


class LanguageRequest(BaseModel):
    text: str


# ── Agent listing ──

@router.get("/agents")
async def list_agents():
    agents = sorted(runner.list_agents(), key=lambda a: (
        0 if a.get("category") == "orchestrator" else 1,
        a.get("name", "")
    ))
    return {"agents": agents, "total": len(agents)}


@router.get("/agents/categories")
async def list_categories():
    cats = runner.get_categories()
    result = {}
    for cat, agent_ids in cats.items():
        result[cat] = [{"id": aid, **AGENT_METADATA.get(aid, {})} for aid in agent_ids]
    return result


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    meta = runner.get_metadata(agent_id)
    if not meta:
        raise HTTPException(404, f"Unknown agent: {agent_id}")
    agent = runner.get_agent(agent_id)
    return {
        "id": agent_id,
        **meta,
        "system_prompt": agent.system_prompt if agent else "",
    }


# ── Orchestration ──

@router.post("/orchestrate")
async def orchestrate(req: OrchestrateRequest):
    """Run a task through the CEO orchestrator — breaks it into phases, assigns specialists, synthesizes results."""
    run = await runner.orchestrate(req.task, req.context)
    return run.to_dict()


@router.get("/orchestrate/runs")
async def get_orch_history(limit: int = Query(20)):
    runs = runner.get_orch_history(limit)
    return {"runs": [r.to_dict() for r in runs], "total": len(runs)}


@router.get("/orchestrate/runs/{run_id}")
async def get_orch_run(run_id: str):
    run = runner.get_orch_run(run_id)
    if not run:
        raise HTTPException(404, "Orchestration run not found")
    return {"run": run.to_dict()}


# ── Single / Batch execution ──

@router.post("/run")
async def run_agent(req: AgentTask):
    agent_run = await runner.run(req.agent, req.task, req.context, req.model)
    return agent_run.to_dict()


@router.post("/run/batch")
async def run_batch(req: BatchTask):
    tasks = [
        {"agent_id": t.agent, "task": t.task, "context": t.context, "model": t.model}
        for t in req.tasks
    ]
    results = await runner.run_batch(tasks)
    return {"runs": [r.to_dict() for r in results], "total": len(results)}


@router.get("/runs")
async def get_history(agent_id: str | None = Query(None), limit: int = Query(50)):
    runs = runner.get_history(agent_id, limit)
    return {"runs": [r.to_dict() for r in runs], "total": len(runs)}


@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    run = runner.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return {"run": run.to_dict()}


@router.get("/teams")
async def list_teams():
    teams: dict[str, list[dict]] = {}
    for agent_id, meta in AGENT_METADATA.items():
        team = meta.get("team", "default")
        if team not in teams:
            teams[team] = []
        teams[team].append({"id": agent_id, **meta})
    return {"teams": teams, "total_teams": len(teams)}


# ── Autonomous Employee ──

@router.post("/employee/handle")
async def employee_handle(req: OrchestrateRequest):
    """Process a natural language request through the full autonomous pipeline."""
    result = await employee.handle_request(req.task, req.context)
    return result


@router.get("/employee/status")
async def employee_status():
    return await employee.status()


# ── Approval Gates ──

@router.get("/approval/pending")
async def get_pending_approvals():
    return {
        "pending": [r.to_dict() for r in approval_gate.get_pending()],
        "total": approval_gate.count_pending(),
    }


@router.get("/approval/history")
async def get_approval_history(limit: int = Query(50)):
    return {
        "history": [r.to_dict() for r in approval_gate.get_history(limit)],
        "total": len(approval_gate.get_history(limit)),
    }


@router.get("/approval/levels")
async def get_approval_levels():
    return {"levels": approval_gate.get_levels()}


@router.post("/approval/approve")
async def approve_request(req: ApprovalAction):
    result = approval_gate.approve(req.request_id, req.note)
    if not result:
        raise HTTPException(404, f"Approval request not found: {req.request_id}")
    return {"status": "approved", "request": result.to_dict(), "message": f"Action '{result.action}' approved."}


@router.post("/approval/deny")
async def deny_request(req: ApprovalAction):
    result = approval_gate.deny(req.request_id, req.note)
    if not result:
        raise HTTPException(404, f"Approval request not found: {req.request_id}")
    return {"status": "denied", "request": result.to_dict(), "message": f"Action '{result.action}' denied."}


@router.put("/approval/levels/{action}")
async def set_approval_level(action: str, level: str = Query(..., pattern="^(auto|notify|confirm|require)$")):
    approval_gate.set_level(action, ApprovalLevel(level))
    return {"action": action, "level": level}


# ── Language ──

@router.post("/language/detect")
async def detect_language(req: LanguageRequest):
    lang = language_engine.detect(req.text)
    return {"code": lang, "name": language_engine.get_name(lang), "text": req.text[:100]}


@router.get("/language/list")
async def list_languages():
    return {"languages": language_engine.list_languages()}


# ── Learning ──

@router.get("/learning/stats")
async def learning_stats():
    return learning_engine.get_stats()


@router.get("/learning/knowledge")
async def get_knowledge(task: str = Query("")):
    if not task:
        return {"best_practices": await learning_engine.get_best_practices()}
    knowledge = await learning_engine.get_knowledge_for_task(task)
    similar = await learning_engine.recall_similar(task, limit=5)
    return {
        "task": task,
        "knowledge": knowledge,
        "similar_count": len(similar),
        "similar": [s.to_dict() for s in similar],
    }


# ── Routine ──

@router.post("/routine/morning")
async def morning_routine():
    return await employee.morning_routine()


@router.post("/routine/evening")
async def evening_routine():
    return await employee.evening_routine()


@router.get("/routine/reports")
async def get_routine_reports(limit: int = Query(7)):
    return {"reports": autonomous_routine.get_reports(limit)}


@router.get("/routine/status")
async def routine_status():
    return {
        "status": autonomous_routine.status,
        "alive": autonomous_routine.is_alive(),
    }
