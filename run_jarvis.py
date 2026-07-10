#!/usr/bin/env python3
"""Jarvis Desktop Companion — tray icon + hotkey for the backend voice system."""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import sys
import threading
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv

    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    load_dotenv(env_path)
except ImportError:
    pass

API_BASE = os.getenv("JARVIS_API", "http://localhost:8000")

HAS_TRAY = False
try:
    import pystray
    from PIL import Image, ImageDraw

    HAS_TRAY = True
except ImportError:
    pass


def api_get(path: str) -> dict | None:
    try:
        with urllib.request.urlopen(f"{API_BASE}{path}", timeout=5) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def api_post(path: str) -> dict | None:
    try:
        req = urllib.request.Request(f"{API_BASE}{path}", data=b"", method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def notify(title: str, message: str) -> None:
    for cmd in [
        ["notify-send", title, message],
        ["dunstify", title, message],
    ]:
        try:
            import subprocess

            subprocess.Popen(cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            return
        except FileNotFoundError:
            continue


class JarvisCompanion:
    def __init__(self):
        self._running = False
        self._tray_icon = None
        self._loop = None
        self._listening = False

    def _on_push_to_talk(self) -> None:
        notify("Jarvis", "Push to talk...")
        result = api_get("/voice/listen/command")
        if result:
            text = result.get("text", "")
            reply = result.get("reply", "")
            if text:
                notify("You", text[:200])
            if reply:
                notify("Jarvis", reply[:200])

    def _toggle_listening(self) -> None:
        status = api_get("/voice/status")
        if status and status.get("listening"):
            api_post("/voice/listen/stop")
            notify("Jarvis", "Paused")
        else:
            api_get("/voice/listen/start")
            notify("Jarvis", "Listening")

    def _open_dashboard(self) -> None:
        import webbrowser

        webbrowser.open("http://localhost:5173/assistant")

    def _quit(self) -> None:
        self._running = False
        if self._tray_icon:
            self._tray_icon.stop()

    def _create_tray_icon(self):
        if not HAS_TRAY:
            return None
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))  # pyright: ignore[reportPossiblyUnboundVariable]
        draw = ImageDraw.Draw(img)  # pyright: ignore[reportPossiblyUnboundVariable]
        draw.ellipse([8, 8, 56, 56], fill=(100, 180, 255, 220))
        draw.ellipse([16, 20, 28, 32], fill=(255, 255, 255, 200))
        draw.ellipse([36, 20, 48, 32], fill=(255, 255, 255, 200))
        draw.arc([20, 34, 44, 50], 0, 180, fill=(255, 255, 255, 200), width=3)

        menu = pystray.Menu(  # pyright: ignore[reportPossiblyUnboundVariable]
            pystray.MenuItem("Toggle Listening", lambda: self._toggle_listening()),  # pyright: ignore[reportPossiblyUnboundVariable]
            pystray.MenuItem("Push to Talk", lambda: self._on_push_to_talk()),  # pyright: ignore[reportPossiblyUnboundVariable]
            pystray.MenuItem("Open Dashboard", lambda: self._open_dashboard()),  # pyright: ignore[reportPossiblyUnboundVariable]
            pystray.MenuItem("Quit", lambda: self._quit()),  # pyright: ignore[reportPossiblyUnboundVariable]
        )
        return pystray.Icon("jarvis", img, "Jarvis", menu)  # pyright: ignore[reportPossiblyUnboundVariable]

    def _run_tray(self):
        if self._tray_icon:
            self._tray_icon.run()

    async def startup(self):
        self._running = True
        self._loop = asyncio.get_running_loop()

        notify("Jarvis", "Starting companion...")

        if HAS_TRAY:
            self._tray_icon = self._create_tray_icon()
            threading.Thread(target=self._run_tray, daemon=True).start()

        notify("Jarvis", "Companion ready")

        try:
            while self._running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass


def main():
    app = JarvisCompanion()
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(app.startup())


if __name__ == "__main__":
    main()
