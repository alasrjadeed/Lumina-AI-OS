from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime

from core.log import log


@dataclass
class Cookie:
    name: str
    value: str
    domain: str = ""
    path: str = "/"
    expires: float = -1
    http_only: bool = False
    secure: bool = False
    same_site: str = "Lax"


@dataclass
class StorageSnapshot:
    local: dict[str, str] = field(default_factory=dict)
    session: dict[str, str] = field(default_factory=dict)


@dataclass
class SessionState:
    url: str = ""
    cookies: list[Cookie] = field(default_factory=list)
    storage: StorageSnapshot = field(default_factory=StorageSnapshot)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class SessionManager:
    """Browser session persistence — cookies, storage, auth state."""

    def __init__(self, page, state_dir: str = ".browser_sessions"):
        self._page = page
        self.state_dir = state_dir
        os.makedirs(state_dir, exist_ok=True)

    async def get_cookies(self) -> list[Cookie]:
        raw = await self._page.context.cookies()
        return [
            Cookie(
                name=c["name"],
                value=c["value"],
                domain=c.get("domain", ""),
                path=c.get("path", "/"),
                expires=c.get("expires", -1),
                http_only=c.get("httpOnly", False),
                secure=c.get("secure", False),
                same_site=c.get("sameSite", "Lax"),
            )
            for c in raw
        ]

    async def set_cookies(self, cookies: list[Cookie]) -> None:
        raw = [
            {
                "name": c.name,
                "value": c.value,
                "domain": c.domain,
                "path": c.path,
                "expires": c.expires,
                "httpOnly": c.http_only,
                "secure": c.secure,
                "sameSite": c.same_site,
            }
            for c in cookies
        ]
        await self._page.context.add_cookies(raw)

    async def clear_cookies(self) -> None:
        await self._page.context.clear_cookies()

    def _camel_to_snake(self, data: list[dict]) -> list[dict]:
        mapping = {"httpOnly": "http_only", "sameSite": "same_site"}
        result = []
        for c in data:
            mapped = {mapping.get(k, k): v for k, v in c.items()}
            result.append(mapped)
        return result

    async def export_cookies(self, path: str) -> str:
        cookies = await self.get_cookies()
        data = [
            {"name": c.name, "value": c.value, "domain": c.domain,
             "path": c.path, "expires": c.expires, "http_only": c.http_only,
             "secure": c.secure, "same_site": c.same_site}
            for c in cookies
        ]
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        log.info("Exported %d cookies to %s", len(cookies), path)
        return path

    async def import_cookies(self, path: str) -> int:
        with open(path) as f:
            data = json.load(f)
        cookies = [Cookie(**c) for c in self._camel_to_snake(data)]
        await self.set_cookies(cookies)
        log.info("Imported %d cookies from %s", len(cookies), path)
        return len(cookies)

    async def get_storage(self) -> StorageSnapshot:
        local = await self._page.evaluate("JSON.stringify(window.localStorage)")
        session = await self._page.evaluate("JSON.stringify(window.sessionStorage)")
        return StorageSnapshot(
            local=json.loads(local) if local else {},
            session=json.loads(session) if session else {},
        )

    async def set_storage_item(self, key: str, value: str, storage: str = "local") -> None:
        if storage == "local":
            await self._page.evaluate(f"window.localStorage.setItem('{key}', '{value}')")
        else:
            await self._page.evaluate(f"window.sessionStorage.setItem('{key}', '{value}')")

    async def clear_storage(self, storage: str = "all") -> None:
        if storage in ("local", "all"):
            await self._page.evaluate("window.localStorage.clear()")
        if storage in ("session", "all"):
            await self._page.evaluate("window.sessionStorage.clear()")

    async def save_session(self, name: str) -> str:
        state = SessionState(
            url=self._page.url,
            cookies=await self.get_cookies(),
            storage=await self.get_storage(),
        )
        path = os.path.join(self.state_dir, f"{name}.json")
        with open(path, "w") as f:
            json.dump({
                "url": state.url,
                "cookies": [
                    {"name": c.name, "value": c.value, "domain": c.domain,
                     "path": c.path, "expires": c.expires, "http_only": c.http_only,
                     "secure": c.secure, "same_site": c.same_site}
                    for c in state.cookies
                ],
                "storage": {"local": state.storage.local, "session": state.storage.session},
                "timestamp": state.timestamp,
            }, f, indent=2)
        log.info("Session saved: %s", name)
        return path

    async def restore_session(self, name: str) -> bool:
        path = os.path.join(self.state_dir, f"{name}.json")
        if not os.path.exists(path):
            log.warning("Session not found: %s", name)
            return False
        with open(path) as f:
            data = json.load(f)
        raw_cookies = data.get("cookies", [])
        cookies = [Cookie(**c) for c in self._camel_to_snake(raw_cookies)]
        if cookies:
            await self.set_cookies(cookies)
        storage = data.get("storage", {})
        for key, value in storage.get("local", {}).items():
            await self.set_storage_item(key, value, "local")
        if data.get("url"):
            await self._page.goto(data["url"])
        log.info("Session restored: %s", name)
        return True

    async def list_sessions(self) -> list[str]:
        return [f.replace(".json", "") for f in os.listdir(self.state_dir) if f.endswith(".json")]

    async def delete_session(self, name: str) -> bool:
        path = os.path.join(self.state_dir, f"{name}.json")
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
