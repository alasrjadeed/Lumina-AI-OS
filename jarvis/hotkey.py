from __future__ import annotations

import contextlib
import threading
from collections.abc import Callable


class HotkeyManager:
    def __init__(self):
        self._listener = None
        self._thread = None
        self._running = False
        self._hotkeys: dict[str, Callable] = {}

    def register(self, combo: str, callback: Callable) -> None:
        self._hotkeys[combo] = callback

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._listener:
            with contextlib.suppress(Exception):
                self._listener.stop()

    def _listen(self) -> None:
        try:
            from pynput import keyboard
        except ImportError:
            return

        def on_press(key):
            try:
                k = key.char
            except AttributeError:
                k = str(key)
            for combo, callback in self._hotkeys.items():
                parts = combo.lower().split("+")
                if _matches_hotkey(parts, k):
                    threading.Thread(target=callback, daemon=True).start()
            return True

        with keyboard.Listener(on_press=on_press) as self._listener:
            self._listener.join()


def _matches_hotkey(parts: list[str], key_str: str) -> bool:
    cleaned = key_str.replace("Key.", "").lower()
    for p in parts:
        p = p.strip().lower()
        if p == "<ctrl>":
            continue
        if p == "<shift>":
            continue
        if p == "<alt>":
            continue
        if p == cleaned:
            return True
    return False
