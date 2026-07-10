"""Advanced Agent Runner API — detailed agent info, streaming, batch, history."""

import json

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.agents.runner import AGENT_METADATA, runner

router = APIRouter(prefix="/agents", tags=["Agents"])


class AgentTask(BaseModel):
    agent: str
    task: str
    context: dict | None = None
    model: str = ""


class BatchTask(BaseModel):
    tasks: list[AgentTask]


@router.get("")
async def list_agents():
    return {"agents": sorted(runner.list_agents(), key=lambda a: a["id"])}


@router.get("/categories")
async def list_categories():
    cats = runner.get_categories()
    result = {}
    for cat, agent_ids in cats.items():
        result[cat] = [{"id": aid, **AGENT_METADATA.get(aid, {})} for aid in agent_ids]
    return result


@router.get("/runs")
async def get_history(agent_id: str | None = Query(None), limit: int = Query(50)):
    runs = runner.get_history(agent_id, limit)
    return {"runs": [r.to_dict() for r in runs], "total": len(runs)}


@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    run = runner.get_run(run_id)
    if not run:
        return {"error": "Run not found"}, 404
    return {"run": run.to_dict()}


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    meta = runner.get_metadata(agent_id)
    if not meta:
        return {"error": f"Unknown agent: {agent_id}"}, 404
    agent = runner.get_agent(agent_id)
    return {
        "id": agent_id,
        **meta,
        "system_prompt": agent.system_prompt if agent else "",
    }


@router.post("/run")
async def run_agent(req: AgentTask):
    run = await runner.run(req.agent, req.task, req.context, req.model)
    return run.to_dict()


@router.post("/run/stream")
async def run_agent_stream(req: AgentTask):
    run = await runner.run(req.agent, req.task, req.context, req.model)

    async def event_stream():
        data = json.dumps(
            {
                "type": "start",
                "run_id": run.run_id,
                "agent_id": run.agent_id,
                "agent_name": run.agent_name,
            }
        )
        yield f"data: {data}\n\n"
        yield f"data: {json.dumps({'type': 'status', 'status': run.status})}\n\n"
        if run.output:
            for chunk in [run.output[i : i + 500] for i in range(0, len(run.output), 500)]:
                yield f"data: {json.dumps({'type': 'output', 'text': chunk})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'run': run.to_dict()})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/run/batch")
async def run_batch(req: BatchTask):
    tasks = [
        {"agent_id": t.agent, "task": t.task, "context": t.context, "model": t.model}
        for t in req.tasks
    ]
    results = await runner.run_batch(tasks)
    return {"runs": [r.to_dict() for r in results], "total": len(results)}
