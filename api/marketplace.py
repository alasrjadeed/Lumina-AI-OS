"""Plugin Marketplace API — browse, install, and manage Lumina plugins."""

from fastapi import APIRouter, Query
from pydantic import BaseModel

from core.marketplace import marketplace

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])


class PluginInstall(BaseModel):
    plugin_id: str


class PluginListingData(BaseModel):
    id: str
    name: str
    version: str = "1.0.0"
    author: str = ""
    description: str = ""
    category: str = "general"
    tags: list[str] = []
    icon: str = "Plug"
    license: str = "MIT"


@router.get("/catalog")
async def browse(category: str = Query(""), query: str = Query(""), sort: str = Query("downloads")):
    results = marketplace.browse(category=category, query=query, sort_by=sort)
    return {
        "plugins": [p.to_dict() for p in results],
        "total": len(results),
        "categories": marketplace.get_categories(),
    }


@router.get("/catalog/{plugin_id}")
async def get_plugin(plugin_id: str):
    plugin = marketplace.get_plugin(plugin_id)
    if not plugin:
        return {"error": f"Plugin not found: {plugin_id}"}, 404
    return {"plugin": plugin.to_dict()}


@router.get("/installed")
async def installed():
    plugins = marketplace.get_installed()
    return {"plugins": [p.to_dict() for p in plugins], "total": len(plugins)}


@router.post("/install")
async def install(req: PluginInstall):
    return marketplace.install(req.plugin_id)


@router.post("/uninstall")
async def uninstall(req: PluginInstall):
    return marketplace.uninstall(req.plugin_id)


@router.post("/update")
async def update(req: PluginInstall):
    return marketplace.update(req.plugin_id)


@router.get("/search")
async def search(q: str = Query("")):
    results = marketplace.search(q)
    return {"plugins": [p.to_dict() for p in results], "total": len(results)}


@router.get("/categories")
async def categories():
    return {"categories": marketplace.get_categories()}


@router.get("/stats")
async def stats():
    return marketplace.get_stats()


@router.post("/catalog/add")
async def add_to_catalog(data: PluginListingData):
    listing = marketplace.add_to_catalog(data.model_dump())
    return {"status": "added", "plugin": listing.to_dict()}


@router.delete("/catalog/{plugin_id}")
async def remove_from_catalog(plugin_id: str):
    removed = marketplace.remove_from_catalog(plugin_id)
    return {"status": "removed" if removed else "not_found"}
