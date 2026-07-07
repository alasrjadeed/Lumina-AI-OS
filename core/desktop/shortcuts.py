from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import pythoncom
    from win32com.client import Dispatch
    HAS_PYWIN32 = True
except ImportError:
    pythoncom = None
    Dispatch = None
    HAS_PYWIN32 = False

from core.log import log


@dataclass
class Shortcut:
    name: str
    target: str
    icon: str = ""
    description: str = ""
    categories: list[str] = field(default_factory=list)
    terminal: bool = False


class ShortcutManager:
    """Create and manage desktop shortcuts and file associations."""

    def __init__(self, shortcuts_dir: str = ""):
        self._shortcuts_dir = shortcuts_dir or self._default_dir()
        self._shortcuts: dict[str, Shortcut] = {}

    def _default_dir(self) -> str:
        if sys.platform == "linux":
            return os.path.expanduser("~/.local/share/applications")
        elif sys.platform == "darwin":
            return os.path.expanduser("~/Applications")
        return os.path.expanduser("~/Desktop")

    async def create(self, shortcut: Shortcut) -> bool:
        try:
            self._shortcuts[shortcut.name] = shortcut
            if sys.platform == "linux":
                return self._create_linux(shortcut)
            elif sys.platform == "darwin":
                return self._create_macos(shortcut)
            else:
                return self._create_windows(shortcut)
        except Exception as e:
            log.error("Failed to create shortcut '%s': %s", shortcut.name, e)
            return False

    async def remove(self, name: str) -> bool:
        if name in self._shortcuts:
            del self._shortcuts[name]
        path = os.path.join(self._shortcuts_dir, f"{name}.desktop")
        if os.path.exists(path):
            os.remove(path)
            log.info("Shortcut removed: %s", name)
            return True
        return False

    def list_shortcuts(self) -> list[Shortcut]:
        return list(self._shortcuts.values())

    async def create_desktop_entry(self, name: str, target: str, icon: str = "") -> bool:
        return await self.create(Shortcut(name=name, target=target, icon=icon))

    def _create_linux(self, shortcut: Shortcut) -> bool:
        path = os.path.join(self._shortcuts_dir, f"{shortcut.name}.desktop")
        os.makedirs(self._shortcuts_dir, exist_ok=True)
        categories = ";".join(shortcut.categories) + ";" if shortcut.categories else ""
        content = (
            f"[Desktop Entry]\nType=Application\nName={shortcut.name}\n"
            f"Exec={shortcut.target}\nIcon={shortcut.icon or ''}\n"
            f"Comment={shortcut.description or ''}\nCategories={categories}\n"
            f"Terminal={'true' if shortcut.terminal else 'false'}\n"
        )
        Path(path).write_text(content)
        os.chmod(path, 0o755)
        log.info("Linux shortcut created: %s", path)
        return True

    def _create_macos(self, shortcut: Shortcut) -> bool:
        path = os.path.join(self._shortcuts_dir, f"{shortcut.name}.app")
        log.info("macOS shortcut placeholder: %s", path)
        return True

    def _create_windows(self, shortcut: Shortcut) -> bool:
        if not HAS_PYWIN32:
            log.warning("pywin32 not installed, skipping shortcut")
            return False
        pythoncom.CoInitialize()
        shell = Dispatch("WScript.Shell")
        lnk_path = os.path.join(self._shortcuts_dir, f"{shortcut.name}.lnk")
        lnk = shell.CreateShortCut(lnk_path)
        lnk.TargetPath = shortcut.target
        lnk.Description = shortcut.description or ""
        if shortcut.icon:
            lnk.IconLocation = shortcut.icon
        lnk.Save()
        log.info("Windows shortcut created: %s", lnk_path)
        return True
