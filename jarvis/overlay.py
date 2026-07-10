from __future__ import annotations

import math
import threading
import tkinter as tk


class VoiceOverlay:
    def __init__(self):
        self._root = None
        self._canvas = None
        self._visible = False
        self._listening = False
        self._thread = None
        self._phase = 0.0

    def _build_ui(self):
        self._root = tk.Tk()
        self._root.title("Jarvis")
        self._root.overrideredirect(True)
        self._root.attributes("-topmost", True)
        self._root.attributes("-transparentcolor", "white")
        self._root.configure(bg="white")

        screen_w = self._root.winfo_screenwidth()
        size = 80
        x = screen_w - size - 20
        y = 20
        self._root.geometry(f"{size}x{size}+{x}+{y}")

        self._canvas = tk.Canvas(
            self._root, width=size, height=size, bg="white", highlightthickness=0
        )
        self._canvas.pack()
        self._draw_idle()

    def _draw_idle(self):
        if not self._canvas:
            return
        self._canvas.delete("all")
        size = 80
        cx, cy = size // 2, size // 2
        r = 12
        self._canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#64B5F6", outline="")
        self._canvas.create_text(cx, cy + 2, text="J", fill="white", font=("Arial", 14, "bold"))

    def _draw_listening(self):
        if not self._canvas:
            return
        self._phase += 0.15
        self._canvas.delete("all")
        size = 80
        cx, cy = size // 2, size // 2
        pulse = 4 * math.sin(self._phase) + 14
        self._canvas.create_oval(
            cx - pulse, cy - pulse, cx + pulse, cy + pulse, fill="#43A047", outline=""
        )
        inner = 6 * math.sin(self._phase * 1.5)
        self._canvas.create_oval(
            cx - inner, cy - inner, cx + inner, cy + inner, fill="#66BB6A", outline=""
        )
        self._canvas.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill="#A5D6A7", outline="")
        if self._listening and self._root is not None:
            self._root.after(80, self._draw_listening)

    def show(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        self._build_ui()
        if self._root is not None:
            self._root.mainloop()

    def set_listening(self, active: bool):
        self._listening = active
        if not self._canvas or self._root is None:
            return
        if active:
            self._root.after(0, self._draw_listening)
        else:
            self._root.after(0, self._draw_idle)

    def hide(self):
        if self._root is not None:
            if self._root:
                self._root.after(0, self._root.destroy)
            self._root = None
