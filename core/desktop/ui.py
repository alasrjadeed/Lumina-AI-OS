from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

try:
    from PySide6.QtWidgets import QApplication, QMainWindow  # pyright: ignore[reportMissingImports]

    HAS_PYSIDE = True
except ImportError:
    QApplication = None
    QMainWindow = None
    HAS_PYSIDE = False

from core.log import log


@dataclass
class WindowState:
    x: int = 100
    y: int = 100
    width: int = 1200
    height: int = 800
    maximized: bool = False
    theme: str = "dark"


class ThemeManager:
    """Manage application themes (dark/light)."""

    def __init__(self):
        self._theme = "dark"
        self._listeners: list[Callable[[str], None]] = []

    @property
    def theme(self) -> str:
        return self._theme

    def set_theme(self, theme: str) -> None:
        if theme not in ("dark", "light"):
            raise ValueError(f"Unknown theme: {theme}")
        self._theme = theme
        for listener in self._listeners:
            listener(theme)
        log.info("Theme changed: %s", theme)

    def toggle(self) -> str:
        new = "light" if self._theme == "dark" else "dark"
        self.set_theme(new)
        return new

    def on_change(self, callback: Callable[[str], None]) -> None:
        self._listeners.append(callback)

    def get_stylesheet(self) -> str:
        if self._theme == "dark":
            return self._dark_stylesheet()
        return self._light_stylesheet()

    def _dark_stylesheet(self) -> str:
        b, s, o, t, st = "#1e1e2e", "#313244", "#45475a", "#cdd6f4", "#a6adc8"
        return (
            f"QMainWindow,QWidget{{background:{b};color:{t};}}"
            f"QPushButton{{background:{o};color:{t};border-radius:4px;padding:6px 12px;}}"
            f"QPushButton:hover{{background:#585b70;}}"
            f"QLineEdit,QTextEdit,QPlainTextEdit{{background:{s};color:{t};"
            f"border:1px solid {o};border-radius:4px;padding:4px;}}"
            f"QListWidget,QTreeWidget{{background:{s};color:{t};border:1px solid {o};}}"
            f"QMenuBar{{background:#181825;color:{t};}}"
            f"QMenu{{background:{s};color:{t};border:1px solid {o};}}"
            f"QMenu::item:selected{{background:{o};}}"
            f"QStatusBar{{background:#181825;color:{st};}}"
            f"QTabWidget::pane{{border:1px solid {o};background:{b};}}"
            f"QTabBar::tab{{background:{s};color:{st};padding:6px 12px;}}"
            f"QTabBar::tab:selected{{background:{o};color:{t};}}"
        )

    def _light_stylesheet(self) -> str:
        b, s, o, t, st = "#eff1f5", "#e6e9ef", "#dce0e8", "#4c4f69", "#6c6f85"
        return (
            f"QMainWindow,QWidget{{background:{b};color:{t};}}"
            f"QPushButton{{background:{o};color:{t};border-radius:4px;padding:6px 12px;}}"
            f"QPushButton:hover{{background:#ccd0da;}}"
            f"QLineEdit,QTextEdit,QPlainTextEdit{{background:{s};color:{t};"
            f"border:1px solid #ccd0da;border-radius:4px;padding:4px;}}"
            f"QListWidget,QTreeWidget{{background:{s};color:{t};border:1px solid #ccd0da;}}"
            f"QMenuBar{{background:{o};color:{t};}}"
            f"QMenu{{background:{s};color:{t};border:1px solid #ccd0da;}}"
            f"QMenu::item:selected{{background:#ccd0da;}}"
            f"QStatusBar{{background:{o};color:{st};}}"
            f"QTabWidget::pane{{border:1px solid #ccd0da;background:{b};}}"
            f"QTabBar::tab{{background:{s};color:{st};padding:6px 12px;}}"
            f"QTabBar::tab:selected{{background:{o};color:{t};}}"
        )


class AppWindow:
    """Main application window manager (works without PySide6 for testing)."""

    def __init__(self, title: str = "Lumina Desktop"):
        self.title = title
        self.state = WindowState()
        self.theme = ThemeManager()
        self._qt_app = None
        self._qt_window = None

    def initialize_pyside(self):
        if not HAS_PYSIDE:
            log.warning("PySide6 not installed")
            return False
        assert QApplication is not None
        self._qt_app = QApplication.instance() or QApplication([])
        self._qt_app.setApplicationName(self.title)
        assert QMainWindow is not None
        self._qt_window = QMainWindow()
        self._qt_window.setWindowTitle(self.title)
        self._qt_window.resize(self.state.width, self.state.height)
        if self.state.maximized:
            self._qt_window.showMaximized()
        else:
            self._qt_window.move(self.state.x, self.state.y)
        return True

    def show(self) -> bool:
        if not self._qt_window and not self.initialize_pyside():
            log.info("AppWindow: running in headless mode")
            return False
        assert self._qt_window is not None
        self._qt_window.show()
        return True

    def set_central_widget(self, widget: Any) -> None:
        if self._qt_window:
            self._qt_window.setCentralWidget(widget)

    def set_menu_bar(self, menu_bar: Any) -> None:
        if self._qt_window:
            self._qt_window.setMenuBar(menu_bar)

    def set_status_bar(self, status_bar: Any) -> None:
        if self._qt_window:
            self._qt_window.setStatusBar(status_bar)

    def apply_theme(self) -> None:
        if self._qt_app:
            self._qt_app.setStyleSheet(self.theme.get_stylesheet())

    def save_state(self, path: str) -> None:
        data = {
            "x": self.state.x,
            "y": self.state.y,
            "width": self.state.width,
            "height": self.state.height,
            "maximized": self.state.maximized,
            "theme": self.theme.theme,
        }
        with open(path, "w") as f:
            json.dump(data, f)

    def load_state(self, path: str) -> None:
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            fields = WindowState.__dataclass_fields__
            self.state = WindowState(**{k: v for k, v in data.items() if k in fields})
            if "theme" in data:
                self.theme.set_theme(data["theme"])
