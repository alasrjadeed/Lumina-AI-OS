from __future__ import annotations

import asyncio
import contextlib
import multiprocessing
import os
import sys
import traceback
from multiprocessing.connection import (
    Connection as MultiprocessingConnection,  # pyright: ignore[reportAttributeAccessIssue]
)
from typing import Any

from kernel.log import setup_log

log = setup_log("plugins.sandbox")

_SANDBOX_TIMEOUT = 30


def _sandbox_target(
    plugin_dir: str,
    module_name: str,
    entry_point: str,
    conn: MultiprocessingConnection,
) -> None:
    """Entry point for the sandbox subprocess."""
    sys.path.insert(0, os.path.dirname(plugin_dir))
    try:
        mod = __import__(module_name)
        cls = getattr(mod, entry_point)
        instance = cls()
    except Exception as exc:
        conn.send({"status": "error", "error": str(exc), "traceback": traceback.format_exc()})
        conn.close()
        return

    conn.send({"status": "ok"})

    while True:
        try:
            if not conn.poll(1):
                continue
            msg = conn.recv()
        except (EOFError, BrokenPipeError):
            break

        cmd = msg.get("cmd")
        if cmd == "stop":
            break

        try:
            method = getattr(instance, cmd, None)
            if method is None:
                conn.send({"status": "error", "error": f"No such method: {cmd}"})
                continue
            result_or_coro = method(*msg.get("args", ()), **msg.get("kwargs", {}))
            if asyncio.iscoroutine(result_or_coro):
                result = asyncio.run(result_or_coro)
            else:
                result = result_or_coro
            conn.send({"status": "ok", "result": result})
        except Exception as exc:
            conn.send({"status": "error", "error": str(exc), "traceback": traceback.format_exc()})

    conn.close()


class SandboxedPlugin:
    def __init__(
        self,
        name: str,
        plugin_dir: str,
        entry_point: str = "main",
        timeout: float = _SANDBOX_TIMEOUT,
    ) -> None:
        self._name = name
        self._plugin_dir = plugin_dir
        self._entry_point = entry_point
        self._timeout = timeout
        self._process: multiprocessing.Process | None = None
        self._conn: MultiprocessingConnection | None = None

    async def start(self) -> None:
        parent_conn, child_conn = multiprocessing.Pipe(duplex=True)
        self._process = multiprocessing.Process(
            target=_sandbox_target,
            args=(self._plugin_dir, self._name, self._entry_point, child_conn),
            daemon=True,
        )
        self._process.start()
        child_conn.close()
        self._conn = parent_conn

        loop = asyncio.get_running_loop()
        assert self._conn is not None
        resp = await loop.run_in_executor(None, self._conn.recv)
        if resp.get("status") != "ok":
            raise RuntimeError(f"Sandbox startup failed for '{self._name}': {resp.get('error')}")
        log.info("Sandbox started: %s (pid=%d)", self._name, self._process.pid)

    async def stop(self) -> None:
        if self._conn is None:
            return
        with contextlib.suppress(Exception):
            self._conn.send({"cmd": "stop"})
        if self._process is not None:
            self._process.join(timeout=5)
            if self._process.is_alive():
                self._process.kill()
                self._process.join()
            self._process.close()
        if self._conn is not None:
            self._conn.close()
        self._process = None
        self._conn = None
        log.info("Sandbox stopped: %s", self._name)

    @property
    def is_alive(self) -> bool:
        return self._process is not None and self._process.is_alive()

    async def call(self, method: str, *args: Any, **kwargs: Any) -> Any:
        if self._conn is None:
            raise RuntimeError(f"Sandbox not started for '{self._name}'")
        loop = asyncio.get_running_loop()

        def _send_recv() -> dict:
            assert self._conn is not None
            self._conn.send({"cmd": method, "args": args, "kwargs": kwargs})
            if not self._conn.poll(self._timeout):
                raise TimeoutError(f"Sandbox call '{method}' timed out after {self._timeout}s")
            return self._conn.recv()

        resp = await loop.run_in_executor(None, _send_recv)
        if resp.get("status") != "ok":
            raise RuntimeError(
                f"Sandbox call '{method}' failed for '{self._name}': {resp.get('error')}"
            )
        return resp.get("result")

    async def ensure_alive(self) -> None:
        if not self.is_alive:
            log.warning("Sandbox process dead for '%s', restarting", self._name)
            await self.start()


class SandboxedPluginLoader:
    def __init__(self, loader: Any, timeout: float = _SANDBOX_TIMEOUT) -> None:
        self._loader = loader
        self._timeout = timeout
        self._sandboxes: dict[str, SandboxedPlugin] = {}

    async def load(self, name: str) -> SandboxedPlugin:
        if name in self._sandboxes:
            return self._sandboxes[name]

        manifest = self._loader.get_manifest(name)
        if manifest is None:
            raise RuntimeError(f"Plugin '{name}' not discovered")

        plugin_dir = None
        for d in self._loader._plugin_dirs:
            candidate = os.path.join(d, name)
            if os.path.isdir(candidate):
                plugin_dir = candidate
                break
        if plugin_dir is None:
            raise RuntimeError(f"Plugin directory not found for '{name}'")

        sandbox = SandboxedPlugin(
            name=name,
            plugin_dir=plugin_dir,
            entry_point=manifest.entry_point,
            timeout=self._timeout,
        )
        await sandbox.start()
        self._sandboxes[name] = sandbox
        return sandbox

    async def unload(self, name: str) -> None:
        sandbox = self._sandboxes.pop(name, None)
        if sandbox is not None:
            await sandbox.stop()

    async def call(self, name: str, method: str, *args: Any, **kwargs: Any) -> Any:
        sandbox = self._sandboxes.get(name)
        if sandbox is None:
            raise RuntimeError(f"Sandbox not found for '{name}'")
        await sandbox.ensure_alive()
        return await sandbox.call(method, *args, **kwargs)

    async def shutdown_all(self) -> None:
        for name in list(self._sandboxes):
            await self.unload(name)
