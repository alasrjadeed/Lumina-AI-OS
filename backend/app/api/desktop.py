from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.app.services.desktop.desktop_service import DesktopService

router = APIRouter()
desktop = DesktopService()


class FileOpRequest(BaseModel):
    path: str


class FileWriteRequest(BaseModel):
    path: str
    content: str


class FileCopyMoveRequest(BaseModel):
    source: str
    destination: str


class ClipboardRequest(BaseModel):
    text: str


@router.get("/files")
async def list_files(path: str = "."):
    return await desktop.list_files(path)


@router.post("/files/read")
async def read_file(req: FileOpRequest):
    return await desktop.read_file(req.path)


@router.post("/files/write")
async def write_file(req: FileWriteRequest):
    return await desktop.write_file(req.path, req.content)


@router.post("/files/copy")
async def copy_file(req: FileCopyMoveRequest):
    return await desktop.copy_file(req.source, req.destination)


@router.post("/files/move")
async def move_file(req: FileCopyMoveRequest):
    return await desktop.move_file(req.source, req.destination)


@router.post("/files/delete")
async def delete_file(req: FileOpRequest):
    return await desktop.delete_file(req.path)


@router.post("/clipboard/copy")
async def clipboard_copy(req: ClipboardRequest):
    return await desktop.clipboard_copy(req.text)


@router.get("/clipboard/paste")
async def clipboard_paste():
    return await desktop.clipboard_paste()


@router.get("/system")
async def system_info():
    return await desktop.get_system_info()


@router.get("/processes")
async def process_list():
    return await desktop.get_process_list()


@router.post("/screenshot")
async def screenshot():
    return await desktop.take_screenshot()
