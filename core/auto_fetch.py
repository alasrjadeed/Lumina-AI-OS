"""Auto-fetch — 20-min background sync: pulls emails, messages, docs into memory."""

from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Callable

from core.log import log
from core.memory.engine import MemoryEngine

_AUTO_FETCH_DIR = os.path.expanduser("~/.lumina/auto_fetch")
_SYNC_INTERVAL = 1200


class SyncState:
    def __init__(self):
        self._last_sync: dict[str, float] = {}
        self._load()

    def _path(self) -> str:
        os.makedirs(_AUTO_FETCH_DIR, exist_ok=True)
        return os.path.join(_AUTO_FETCH_DIR, "sync_state.json")

    def _load(self) -> None:
        path = self._path()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    self._last_sync = json.load(f)
            except Exception:
                pass

    def _save(self) -> None:
        with open(self._path(), "w") as f:
            json.dump(self._last_sync, f, indent=2)

    def last_sync(self, source: str) -> float:
        return self._last_sync.get(source, 0.0)

    def mark_synced(self, source: str) -> None:
        self._last_sync[source] = time.time()
        self._save()


_sync_state = SyncState()

_SyncResult = dict[str, Any]


class AutoFetchSource:
    def __init__(self, name: str, fetch_fn: Callable[[float], list[_SyncResult]]):
        self.name = name
        self.fetch_fn = fetch_fn


_sources: list[AutoFetchSource] = []


def register_source(name: str, fetch_fn: Callable[[float], list[_SyncResult]]) -> None:
    _sources.append(AutoFetchSource(name=name, fetch_fn=fetch_fn))


async def auto_fetch_loop(
    memory: MemoryEngine | None = None,
    on_sync: Callable[[str, list[_SyncResult]], Any] | None = None,
):
    log.info("Auto-fetch loop started (interval: %ds)", _SYNC_INTERVAL)

    while True:
        try:
            for source in _sources:
                try:
                    since = _sync_state.last_sync(source.name)

                    if asyncio.iscoroutinefunction(source.fetch_fn):
                        items = await source.fetch_fn(since)
                    else:
                        items = source.fetch_fn(since)

                    if items:
                        log.info("Auto-fetch %s: %d new items", source.name, len(items))

                        if memory:
                            for item in items[:20]:
                                content = item.get("content") or item.get("text") or json.dumps(item)
                                metadata = {k: v for k, v in item.items() if k not in ("content", "text")}
                                await memory.record_episode(
                                    task=f"auto_fetch:{source.name}",
                                    agent="auto_fetch",
                                    action=f"sync_{source.name}",
                                    result=content[:500],
                                    success=True,
                                )

                        if on_sync:
                            if asyncio.iscoroutinefunction(on_sync):
                                await on_sync(source.name, items)
                            else:
                                on_sync(source.name, items)

                    _sync_state.mark_synced(source.name)

                except Exception as e:
                    log.warning("Auto-fetch source %s error: %s", source.name, e)

        except asyncio.CancelledError:
            log.info("Auto-fetch loop cancelled")
            break
        except Exception as e:
            log.warning("Auto-fetch loop error: %s", e)

        await asyncio.sleep(_SYNC_INTERVAL)
