from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None

from core.log import log


@dataclass
class BrowserProfile:
    name: str
    data_dir: str = ""
    headless: bool = True
    proxy: str = ""
    args: list[str] = field(default_factory=list)
    viewport: dict[str, int] = field(default_factory=lambda: {"width": 1280, "height": 720})
    locale: str = "en-US"
    timezone: str = ""


class BrowserManager:
    """Manage multiple browser instances, profiles, and launch configurations."""

    def __init__(self, profiles_dir: str = ".browser_profiles"):
        self.profiles_dir = profiles_dir
        self._profiles: dict[str, BrowserProfile] = {}
        self._instances: dict[str, Any] = {}
        self._active: str = ""
        os.makedirs(profiles_dir, exist_ok=True)

    def register_profile(self, profile: BrowserProfile) -> None:
        self._profiles[profile.name] = profile
        log.info("Browser profile registered: %s", profile.name)

    def get_profile(self, name: str) -> BrowserProfile | None:
        return self._profiles.get(name)

    def list_profiles(self) -> list[str]:
        return list(self._profiles.keys())

    def remove_profile(self, name: str) -> bool:
        if name in self._profiles:
            del self._profiles[name]
            return True
        return False

    def default_profile(self) -> BrowserProfile:
        return BrowserProfile(
            name="default",
            data_dir=os.path.join(self.profiles_dir, "default"),
        )

    async def launch(self, profile_name: str = "default") -> Any:
        profile = self._profiles.get(profile_name) or self.default_profile()
        if async_playwright is None:
            raise ImportError("playwright is required")
        p = await async_playwright().start()
        launch_args = profile.args.copy()
        if profile.proxy:
            launch_args.append(f"--proxy-server={profile.proxy}")
        browser = await p.chromium.launch(
            headless=profile.headless,
            args=launch_args,
        )
        context = await browser.new_context(
            viewport=profile.viewport,
            locale=profile.locale,
            timezone_id=profile.timezone or None,
        )
        page = await context.new_page()
        instance = {
            "playwright": p,
            "browser": browser,
            "context": context,
            "page": page,
            "profile": profile_name,
        }
        self._instances[profile_name] = instance
        self._active = profile_name
        log.info("Browser launched: %s (headless=%s)", profile_name, profile.headless)
        return page

    async def close(self, profile_name: str = "") -> None:
        names = [profile_name] if profile_name else list(self._instances.keys())
        for name in names:
            inst = self._instances.pop(name, None)
            if inst:
                await inst["browser"].close()
                await inst["playwright"].stop()
                log.info("Browser closed: %s", name)
        if self._active in names:
            self._active = ""

    async def close_all(self) -> None:
        await self.close()

    def active_page(self) -> Any:
        inst = self._instances.get(self._active)
        return inst["page"] if inst else None

    def active_instance(self) -> dict | None:
        return self._instances.get(self._active)

    def switch_profile(self, name: str) -> bool:
        if name in self._instances:
            self._active = name
            return True
        return False

    def list_instances(self) -> list[str]:
        return list(self._instances.keys())

    async def new_page(self, profile_name: str = "") -> Any:
        name = profile_name or self._active
        inst = self._instances.get(name)
        if not inst:
            return None
        page = await inst["context"].new_page()
        return page

    def get_context(self, profile_name: str = "") -> Any:
        name = profile_name or self._active
        inst = self._instances.get(name)
        return inst["context"] if inst else None
