"""Personal Data Vault API — store once, use everywhere."""

from fastapi import APIRouter
from pydantic import BaseModel

from core.vault.store import VaultProfile, vault

router = APIRouter(prefix="/vault", tags=["Vault"])


class VaultItem(BaseModel):
    key: str
    value: str


@router.get("/")
async def get_all():
    return {"data": vault.all(), "count": vault.count(), "missing": vault.missing_required()}


@router.post("/")
async def set_item(req: VaultItem):
    vault.set(req.key, req.value)
    return {"status": "ok", "key": req.key}


@router.post("/bulk")
async def set_bulk(items: dict[str, str]):
    vault.set_many(items)
    return {"status": "ok", "updated": len(items)}


@router.delete("/{key}")
async def delete_item(key: str):
    return {"deleted": vault.delete(key)}


@router.get("/profile")
async def get_profile():
    return vault.get_profile().__dict__


@router.post("/profile")
async def set_profile(profile: VaultProfile):
    vault.set_profile(profile)
    return {"status": "ok"}


@router.get("/prompt")
async def get_prompt():
    return {"prompt": vault.to_context_prompt()}


@router.post("/fill")
async def fill_text(text: str):
    return {"result": vault.fill_template(text)}
