"""Browser automation — Playwright-based web interaction suite.

Includes page navigation, element finding, session management, network
interception, screenshots, downloads, DOM manipulation, and a unified
AutomationAPI combining all modules.
"""

from core.browser.automation import BrowserAutomation, browser
from core.browser.automation_api import AutomationAPI
from core.browser.browser_manager import BrowserManager, BrowserProfile
from core.browser.dom_interaction import DOMInteraction
from core.browser.downloads import DownloadInfo, DownloadManager
from core.browser.finder import ElementFinder, ElementInfo
from core.browser.form_filler import FormFiller, form_filler
from core.browser.monitor import ConsoleEntry, PageMonitor, PerformanceMetrics
from core.browser.network import NetworkInterceptor, RequestInfo, ResponseInfo
from core.browser.page import PageInteractor, ScrollDirection, WaitStrategy
from core.browser.screenshots import ScreenshotInfo, ScreenshotManager
from core.browser.session import Cookie, SessionManager, SessionState, StorageSnapshot
from core.browser.tab_manager import TabInfo, TabManager

__all__ = [
    "BrowserAutomation",
    "browser",
    "BrowserManager",
    "BrowserProfile",
    "TabManager",
    "TabInfo",
    "AutomationAPI",
    "DownloadManager",
    "DownloadInfo",
    "ScreenshotManager",
    "ScreenshotInfo",
    "DOMInteraction",
    "PageInteractor",
    "WaitStrategy",
    "ScrollDirection",
    "SessionManager",
    "Cookie",
    "SessionState",
    "StorageSnapshot",
    "NetworkInterceptor",
    "RequestInfo",
    "ResponseInfo",
    "ElementFinder",
    "ElementInfo",
    "FormFiller",
    "form_filler",
    "PageMonitor",
    "ConsoleEntry",
    "PerformanceMetrics",
]
