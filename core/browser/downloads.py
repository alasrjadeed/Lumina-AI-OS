from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DownloadInfo:
    url: str
    path: str = ""
    filename: str = ""
    size: int = 0
    completed: bool = False
    mime_type: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0


class DownloadManager:
    """Track and manage file downloads."""

    def __init__(self, page, download_dir: str = ".browser_downloads"):
        self._page = page
        self.download_dir = download_dir
        self._downloads: list[DownloadInfo] = []
        self._pending: dict[str, DownloadInfo] = {}
        os.makedirs(download_dir, exist_ok=True)

    async def start_tracking(self) -> None:
        async def on_download(download):
            info = DownloadInfo(
                url=download.url,
                filename=download.suggested_filename,
                mime_type=download.mime_type or "",
            )
            self._pending[download.url] = info
            self._downloads.append(info)
            path = os.path.join(self.download_dir, info.filename)
            await download.save_as(path)
            info.path = path
            info.completed = True
            info.size = Path(path).stat().st_size if Path(path).exists() else 0
            info.end_time = time.time()
            self._pending.pop(download.url, None)

        self._page.on("download", on_download)

    async def stop_tracking(self) -> None:
        pass

    def get_downloads(self, completed_only: bool = False) -> list[DownloadInfo]:
        if completed_only:
            return [d for d in self._downloads if d.completed]
        return list(self._downloads)

    def get_pending(self) -> list[DownloadInfo]:
        return list(self._pending.values())

    def get_by_filename(self, pattern: str) -> list[DownloadInfo]:
        return [d for d in self._downloads if pattern.lower() in d.filename.lower()]

    def get_by_mime(self, mime_type: str) -> list[DownloadInfo]:
        return [d for d in self._downloads if mime_type in d.mime_type]

    async def wait_for_download(
        self,
        url_pattern: str = "",
        timeout: float = 30000,
    ) -> DownloadInfo | None:
        deadline = time.time() + timeout / 1000
        while time.time() < deadline:
            for d in self._downloads:
                if d.completed and (not url_pattern or url_pattern in d.url):
                    return d
            await asyncio.sleep(0.1)
        return None

    def clear_history(self) -> None:
        self._downloads.clear()
        self._pending.clear()

    async def set_download_path(self, path: str) -> None:
        self.download_dir = path
        os.makedirs(path, exist_ok=True)
        await self._page.context.set_extra_http_headers({})
