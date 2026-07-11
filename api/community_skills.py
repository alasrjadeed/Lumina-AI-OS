"""Community Skills API — browse, import, remove, upgrade from skills.sh ecosystem."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.skills.community import community, catalog

router = APIRouter(prefix="/community-skills", tags=["Community Skills"])


class ImportRequest(BaseModel):
    repo: str
    name: str = ""


@router.get("", summary="Browse community skills from skills.sh ecosystem")
async def browse_skills(query: str = "", limit: int = 50):
    skills = await community.browse(query=query, limit=limit)
    return {
        "skills": [s.to_dict() for s in skills],
        "total": len(skills),
        "installed": community.to_dict()["installed"],
    }


@router.post("/import", summary="Import a skill from a community repo")
async def import_skill(req: ImportRequest):
    if not req.repo:
        raise HTTPException(400, "repo is required")
    return community.import_skill(req.repo, req.name)


@router.post("/{skill_id}/remove", summary="Remove an imported community skill")
async def remove_skill(skill_id: str):
    return community.remove_skill(skill_id)


@router.post("/{skill_id}/upgrade", summary="Upgrade a community skill to latest version")
async def upgrade_skill(skill_id: str):
    return community.upgrade_skill(skill_id)


@router.get("/installed", summary="List installed community skills")
async def list_installed():
    installed = [s.to_dict() for s in community.list_community_skills() if s.installed]
    return {"installed": installed, "count": len(installed)}
