from __future__ import annotations

import os
import shutil
import signal
import subprocess
import time
from dataclasses import dataclass, field

from core.log import log


@dataclass
class AppInfo:
    name: str
    path: str = ""
    pid: int = 0
    running: bool = False
    started: float = field(default_factory=time.time)
    args: list[str] = field(default_factory=list)


class AppManager:
    """Launch, track, and manage desktop applications."""

    def __init__(self):
        self._apps: dict[str, AppInfo] = {}
        self._processes: dict[str, subprocess.Popen] = {}

    def is_installed(self, name: str) -> bool:
        return shutil.which(name) is not None

    async def launch(
        self, name: str, path: str = "",
        args: list[str] | None = None, wait: bool = False,
    ) -> bool:
        executable = path or name
        if not shutil.which(executable) and not os.path.exists(executable):
            log.warning("App not found: %s", executable)
            return False
        try:
            proc = subprocess.Popen(
                [executable] + (args or []),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            info = AppInfo(name=name, path=executable, pid=proc.pid, running=True)
            self._apps[name] = info
            self._processes[name] = proc
            log.info("Launched: %s (pid=%d)", name, proc.pid)
            if wait:
                proc.wait()
            return True
        except Exception as e:
            log.error("Failed to launch %s: %s", name, e)
            return False

    async def kill(self, name: str, force: bool = False) -> bool:
        proc = self._processes.get(name)
        if proc and proc.poll() is None:
            if force:
                proc.kill()
            else:
                proc.terminate()
            proc.wait(timeout=5)
            self._apps[name].running = False
            log.info("Killed: %s", name)
            return True
        return False

    async def kill_by_pid(self, pid: int) -> bool:
        try:
            os.kill(pid, signal.SIGTERM)
            return True
        except ProcessLookupError:
            return False

    def is_running(self, name: str) -> bool:
        proc = self._processes.get(name)
        return proc is not None and proc.poll() is None

    def list_apps(self, running_only: bool = False) -> list[AppInfo]:
        if running_only:
            return [a for a in self._apps.values() if a.running]
        return list(self._apps.values())

    def get_app(self, name: str) -> AppInfo | None:
        return self._apps.get(name)

    async def wait_for_exit(self, name: str, timeout: float = 30) -> bool:
        proc = self._processes.get(name)
        if proc:
            try:
                proc.wait(timeout=timeout)
                self._apps[name].running = False
                return True
            except subprocess.TimeoutExpired:
                return False
        return True

    async def launch_and_wait(
        self, name: str, path: str = "",
        args: list[str] | None = None,
    ) -> int:
        if await self.launch(name, path, args, wait=True):
            proc = self._processes.get(name)
            return proc.returncode if proc else -1
        return -1

    def clear_finished(self) -> None:
        finished = [n for n, p in self._processes.items() if p.poll() is not None]
        for name in finished:
            self._apps[name].running = False
            log.info("Process finished: %s", name)
