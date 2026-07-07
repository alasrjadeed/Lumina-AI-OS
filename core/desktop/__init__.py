"""Desktop automation — OS-level operations and UI components.

File operations, app lifecycle, clipboard, notifications, window
management, PySide6 UI framework, chat interface, settings,
plugin system, and structured logging.
"""

from core.desktop.app_manager import AppInfo, AppManager
from core.desktop.chat import ChatHistory, ChatMessage, ChatSession
from core.desktop.clipboard import ClipboardManager
from core.desktop.logs import LogEntry, LogLevel, LogManager
from core.desktop.notifications import Notification, NotificationManager
from core.desktop.os_automation import DesktopAutomation, desktop
from core.desktop.plugin_manager import PluginInfo, PluginManager, PluginMetadata
from core.desktop.settings import AppSettings, SettingDefinition
from core.desktop.shortcuts import Shortcut, ShortcutManager
from core.desktop.ui import AppWindow, ThemeManager, WindowState
from core.desktop.ui_notifications import (
    NotificationSeverity,
    UINotification,
    UINotificationManager,
)
from core.desktop.window_manager import WindowInfo, WindowManager

__all__ = [
    "DesktopAutomation",
    "desktop",
    "AppManager",
    "AppInfo",
    "ClipboardManager",
    "NotificationManager",
    "Notification",
    "ShortcutManager",
    "Shortcut",
    "WindowManager",
    "WindowInfo",
    "AppWindow",
    "ThemeManager",
    "WindowState",
    "ChatHistory",
    "ChatMessage",
    "ChatSession",
    "AppSettings",
    "SettingDefinition",
    "PluginManager",
    "PluginMetadata",
    "PluginInfo",
    "UINotificationManager",
    "UINotification",
    "NotificationSeverity",
    "LogManager",
    "LogEntry",
    "LogLevel",
]
