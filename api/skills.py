"""Skills API — discover, install, and run agent skills."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.skills.catalog import catalog

router = APIRouter(prefix="/skills", tags=["Skills"])


class InstallRequest(BaseModel):
    name: str
    url: str


@router.get("", summary="List all skills in the catalog")
async def list_skills(tag: str | None = None):
    return {
        "skills": [s.to_dict() for s in catalog.list_skills(tag=tag)],
        "total": len(catalog.list_skills(tag=tag)),
        "sources": [s.to_dict() for s in catalog.list_sources()],
    }


@router.get("/{name}", summary="Get a specific skill by name")
async def get_skill(name: str):
    skill = catalog.get_skill(name)
    if not skill:
        raise HTTPException(404, f"Skill '{name}' not found")
    return skill.to_dict()


@router.post("/install", summary="Install skills from an external source")
async def install_skills(req: InstallRequest):
    try:
        source = catalog.install_from_url(req.name, req.url)
        return {"status": "ok", "source": source.name, "skills": len(source.skills)}
    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("/sources", summary="List all skill sources")
async def list_sources():
    return {"sources": [s.to_dict() for s in catalog.list_sources()]}
