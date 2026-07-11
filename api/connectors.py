"""Connectors API — OAuth-based external service integrations."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.connectors import connector_manager

router = APIRouter(prefix="/connectors", tags=["Connectors"])


class ConnectRequest(BaseModel):
    auth_code: str = ""


@router.get("", summary="List all available connectors")
async def list_connectors():
    return connector_manager.to_dict()


@router.get("/{name}", summary="Get connector details")
async def get_connector(name: str):
    connector = connector_manager.get_connector(name)
    if not connector:
        raise HTTPException(404, f"Connector '{name}' not found")
    return connector.to_dict()


@router.post("/{name}/connect", summary="Connect to an external service")
async def connect_connector(name: str, req: ConnectRequest):
    success = connector_manager.connect(name, req.auth_code)
    if not success:
        raise HTTPException(400, f"Failed to connect '{name}'")
    return {"status": "ok", "name": name, "connected": True}


@router.post("/{name}/disconnect", summary="Disconnect from an external service")
async def disconnect_connector(name: str):
    success = connector_manager.disconnect(name)
    if not success:
        raise HTTPException(400, f"Failed to disconnect '{name}'")
    return {"status": "ok", "name": name, "connected": False}


@router.get("/{name}/fetch", summary="Fetch data from a connected service")
async def fetch_connector(name: str, endpoint: str = ""):
    data = await connector_manager.fetch(name, endpoint)
    if data is None:
        raise HTTPException(400, f"Connector '{name}' not connected or not found")
    return data
