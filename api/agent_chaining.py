from fastapi import APIRouter, HTTPException

from core.agent_chaining import chain_store

router = APIRouter(prefix="/chains", tags=["Agent Chaining"])


@router.get("")
async def list_chains():
    return {"chains": [c.to_dict() for c in chain_store.list()]}


@router.post("")
async def create_chain(name: str, description: str = ""):
    chain = chain_store.create(name=name, description=description)
    return {"chain": chain.to_dict()}


@router.get("/{chain_id}")
async def get_chain(chain_id: str):
    chain = chain_store.get(chain_id)
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    return {"chain": chain.to_dict()}


@router.patch("/{chain_id}")
async def update_chain(chain_id: str, name: str | None = None, description: str | None = None):
    kwargs = {}
    if name is not None:
        kwargs["name"] = name
    if description is not None:
        kwargs["description"] = description
    chain = chain_store.update(chain_id, **kwargs)
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    return {"chain": chain.to_dict()}


@router.delete("/{chain_id}")
async def delete_chain(chain_id: str):
    ok = chain_store.delete(chain_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Chain not found")
    return {"deleted": True}


@router.post("/{chain_id}/steps")
async def add_step(chain_id: str, agent: str, prompt: str, depends_on: str = ""):
    depends = [d.strip() for d in depends_on.split(",") if d.strip()] if depends_on else []
    step_id = chain_store.add_step(chain_id, agent=agent, prompt=prompt, depends_on=depends)
    if not step_id:
        raise HTTPException(status_code=404, detail="Chain not found")
    return {"step_id": step_id}


@router.post("/{chain_id}/steps/{step_id}/output")
async def update_step_output(chain_id: str, step_id: str, output: str):
    ok = chain_store.update_step_output(chain_id, step_id, output=output)
    if not ok:
        raise HTTPException(status_code=404, detail="Step not found")
    return {"updated": True}
