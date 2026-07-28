from __future__ import annotations

import base64
import os
import time
import uuid
from pathlib import Path
from typing import Any

_UPLOAD_DIR = Path(os.path.expanduser("~/.lumina/uploads"))
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED_EXTENSIONS = {
    "image": [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"],
    "audio": [".mp3", ".wav", ".ogg", ".m4a", ".flac"],
    "video": [".mp4", ".webm", ".avi", ".mov"],
    "document": [".pdf", ".docx", ".txt", ".md", ".csv", ".json", ".xml", ".html"],
}

MAX_FILE_SIZE = 50 * 1024 * 1024


def is_supported(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    for category, exts in SUPPORTED_EXTENSIONS.items():
        if ext in exts:
            return True
    return False


def get_category(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    for category, exts in SUPPORTED_EXTENSIONS.items():
        if ext in exts:
            return category
    return "unknown"


def process_upload(file_data: bytes, filename: str) -> dict:
    file_id = uuid.uuid4().hex[:12]
    ext = Path(filename).suffix.lower()
    category = get_category(filename)
    stored_name = f"{file_id}{ext}"
    file_path = _UPLOAD_DIR / stored_name

    with open(file_path, "wb") as f:
        f.write(file_data)

    size_kb = len(file_data) / 1024
    b64 = base64.b64encode(file_data).decode("utf-8") if category == "image" else ""

    return {
        "id": file_id,
        "filename": filename,
        "stored_name": stored_name,
        "category": category,
        "size_kb": round(size_kb, 1),
        "mime_type": _guess_mime(ext),
        "base64": b64,
        "path": str(file_path),
        "uploaded_at": time.time(),
    }


def _guess_mime(ext: str) -> str:
    return {
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml",
        ".mp3": "audio/mpeg", ".wav": "audio/wav", ".ogg": "audio/ogg",
        ".m4a": "audio/mp4", ".flac": "audio/flac",
        ".mp4": "video/mp4", ".webm": "video/webm", ".avi": "video/x-msvideo",
        ".mov": "video/quicktime",
        ".pdf": "application/pdf", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain", ".md": "text/markdown", ".csv": "text/csv",
        ".json": "application/json", ".xml": "application/xml", ".html": "text/html",
    }.get(ext, "application/octet-stream")


def list_uploads(category: str | None = None) -> list[dict]:
    results = []
    for f in _UPLOAD_DIR.iterdir():
        if f.is_file():
            entry = {
                "id": f.stem,
                "stored_name": f.name,
                "category": get_category(f.name),
                "size_kb": round(f.stat().st_size / 1024, 1),
                "uploaded_at": f.stat().st_mtime,
            }
            if category is None or entry["category"] == category:
                results.append(entry)
    results.sort(key=lambda x: x["uploaded_at"], reverse=True)
    return results


def get_upload(file_id: str) -> dict | None:
    for f in _UPLOAD_DIR.iterdir():
        if f.stem == file_id:
            with open(f, "rb") as fh:
                data = fh.read()
            b64 = base64.b64encode(data).decode("utf-8") if get_category(f.name) == "image" else ""
            return {
                "id": f.stem,
                "filename": f.name,
                "category": get_category(f.name),
                "size_kb": round(f.stat().st_size / 1024, 1),
                "base64": b64,
                "uploaded_at": f.stat().st_mtime,
            }
    return None


def delete_upload(file_id: str) -> bool:
    for f in _UPLOAD_DIR.iterdir():
        if f.stem == file_id:
            f.unlink()
            return True
    return False
