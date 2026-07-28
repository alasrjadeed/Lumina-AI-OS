from fastapi import APIRouter, File, HTTPException, UploadFile

from core.multi_modal import (
    delete_upload,
    get_upload,
    is_supported,
    list_uploads,
    process_upload,
)

router = APIRouter(prefix="/uploads", tags=["Multi-modal"])


@router.post("")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename or not is_supported(file.filename):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.filename}")
    data = await file.read()
    if len(data) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")
    result = process_upload(data, file.filename)
    return {"file": result}


@router.get("")
async def list_files(category: str | None = None):
    return {"files": list_uploads(category), "total": len(list_uploads(category))}


@router.get("/{file_id}")
async def get_file(file_id: str):
    entry = get_upload(file_id)
    if not entry:
        raise HTTPException(status_code=404, detail="File not found")
    return {"file": entry}


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    ok = delete_upload(file_id)
    return {"deleted": ok}
