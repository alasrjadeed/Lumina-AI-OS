from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.browser.automation_api import AutomationAPI
from core.browser.browser_manager import BrowserManager, BrowserProfile
from core.browser.dom_interaction import DOMInteraction
from core.browser.downloads import DownloadInfo, DownloadManager
from core.browser.screenshots import ScreenshotManager
from core.browser.tab_manager import TabManager


class AsyncMockPage:
    def __init__(self):
        self._mocks: dict[str, AsyncMock] = {}
        self.context = MagicMock()
        self.context.pages = []
        self.url = "https://example.com"
        self.keyboard = MagicMock()
        self._event_handlers: dict[str, list] = {}

    def on(self, event: str, handler):
        self._event_handlers.setdefault(event, []).append(handler)

    def remove_listener(self, event: str, handler):
        handlers = self._event_handlers.get(event, [])
        if handler in handlers:
            handlers.remove(handler)

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self._mocks:
            self._mocks[name] = AsyncMock()
        return self._mocks[name]


@pytest.fixture
def mock_page():
    return AsyncMockPage()


class TestBrowserManager:
    def test_register_and_get_profile(self):
        bm = BrowserManager()
        profile = BrowserProfile(name="test")
        bm.register_profile(profile)
        assert bm.get_profile("test") is profile
        assert "test" in bm.list_profiles()

    def test_remove_profile(self):
        bm = BrowserManager()
        bm.register_profile(BrowserProfile(name="del"))
        assert bm.remove_profile("del")
        assert not bm.remove_profile("nonexistent")

    def test_default_profile(self):
        bm = BrowserManager()
        dp = bm.default_profile()
        assert dp.name == "default"

    def test_switch_profile(self):
        bm = BrowserManager()
        assert not bm.switch_profile("missing")
        bm._instances["p1"] = {}
        bm._instances["p2"] = {}
        assert bm.switch_profile("p2")
        assert bm._active == "p2"

    def test_list_instances(self):
        bm = BrowserManager()
        bm._instances["a"] = {}
        bm._instances["b"] = {}
        assert set(bm.list_instances()) == {"a", "b"}

    def test_active_page_returns_none_when_no_active(self):
        bm = BrowserManager()
        assert bm.active_page() is None

    def test_active_instance(self):
        bm = BrowserManager()
        bm._instances["active"] = {"page": "p"}
        bm._active = "active"
        assert bm.active_instance() == {"page": "p"}


@pytest.mark.asyncio
class TestTabManager:
    async def test_count(self, mock_page):
        mock_page.context.pages = [mock_page, MagicMock()]
        tm = TabManager(mock_page)
        count = await tm.count()
        assert count == 2

    async def test_list_tabs(self, mock_page):
        p2 = MagicMock()
        p2.url = "https://other.com"
        p2.title = AsyncMock(return_value="Other Page")
        mock_page.context.pages = [mock_page, p2]
        tm = TabManager(mock_page)
        tabs = await tm.list_tabs()
        assert len(tabs) == 2
        assert tabs[0].active

    async def test_switch_to(self, mock_page):
        p2 = MagicMock()
        p2.bring_to_front = AsyncMock()
        mock_page.context.pages = [mock_page, p2]
        tm = TabManager(mock_page)
        assert await tm.switch_to(1)
        p2.bring_to_front.assert_called_once()

    async def test_switch_to_invalid_index(self, mock_page):
        mock_page.context.pages = [mock_page]
        tm = TabManager(mock_page)
        assert not await tm.switch_to(5)

    async def test_open_new_tab(self, mock_page):
        new_page = MagicMock()
        new_page.goto = AsyncMock()
        mock_page.context.new_page = AsyncMock(return_value=new_page)
        tm = TabManager(mock_page)
        result = await tm.open("https://example.com", background=True)
        assert result is new_page

    async def test_duplicate(self, mock_page):
        new_page = MagicMock()
        new_page.goto = AsyncMock()
        mock_page.context.new_page = AsyncMock(return_value=new_page)
        tm = TabManager(mock_page)
        result = await tm.duplicate()
        new_page.goto.assert_called_with("https://example.com")
        assert result is new_page

    async def test_get_by_url(self, mock_page):
        p2 = MagicMock()
        p2.url = "https://docs.example.com/page"
        p2.title = AsyncMock(return_value="Docs")
        mock_page.context.pages = [mock_page, p2]
        tm = TabManager(mock_page)
        results = await tm.get_by_url("docs")
        assert len(results) == 1
        assert "docs" in results[0].url

    async def test_get_by_title(self, mock_page):
        mock_page.title = AsyncMock(return_value="Main Page")
        p2 = MagicMock()
        p2.url = "https://x.com"
        p2.title = AsyncMock(return_value="Settings Page")
        mock_page.context.pages = [mock_page, p2]
        tm = TabManager(mock_page)
        results = await tm.get_by_title("settings")
        assert len(results) == 1


@pytest.mark.asyncio
class TestAutomationAPI:
    async def test_navigate(self, mock_page):
        api = AutomationAPI(mock_page)
        result = await api.navigate("https://example.com")
        assert result is api
        mock_page.goto.assert_called_with("https://example.com", wait_until="networkidle")

    async def test_click(self, mock_page):
        api = AutomationAPI(mock_page)
        result = await api.click("#btn")
        assert result is api
        mock_page.click.assert_called_with("#btn")

    async def test_fill(self, mock_page):
        api = AutomationAPI(mock_page)
        result = await api.fill("#input", "hello")
        mock_page.fill.assert_called_with("#input", "hello")
        assert result is api

    async def test_extract_text(self, mock_page):
        mock_page.inner_text = AsyncMock(return_value="Hello World")
        api = AutomationAPI(mock_page)
        text = await api.extract_text("#el")
        assert text == "Hello World"

    async def test_get_title(self, mock_page):
        mock_page.title = AsyncMock(return_value="Test Page")
        api = AutomationAPI(mock_page)
        assert await api.get_title() == "Test Page"

    async def test_get_url(self, mock_page):
        api = AutomationAPI(mock_page)
        assert await api.get_url() == "https://example.com"


class TestDownloadManager:
    @pytest.mark.asyncio
    async def test_tracking(self, mock_page):
        dm = DownloadManager(mock_page)
        await dm.start_tracking()
        assert len(dm.get_downloads()) == 0

    def test_get_downloads_empty(self):
        dm = DownloadManager(MagicMock())
        assert dm.get_downloads() == []
        assert dm.get_pending() == []

    def test_get_by_filename(self):
        dm = DownloadManager(MagicMock())
        dm._downloads = [DownloadInfo(url="https://x.com/file.pdf", filename="report.pdf")]
        results = dm.get_by_filename("report")
        assert len(results) == 1
        results = dm.get_by_filename("nope")
        assert len(results) == 0

    def test_get_by_mime(self):
        dm = DownloadManager(MagicMock())
        dm._downloads = [
            DownloadInfo(url="https://x.com", filename="img.png", mime_type="image/png"),
        ]
        assert len(dm.get_by_mime("image")) == 1
        assert len(dm.get_by_mime("text")) == 0

    def test_clear_history(self):
        dm = DownloadManager(MagicMock())
        dm._downloads.append(DownloadInfo(url="https://x.com", filename="f"))
        dm.clear_history()
        assert len(dm.get_downloads()) == 0


class TestScreenshotManager:
    @pytest.mark.asyncio
    async def test_capture(self, mock_page, tmp_path: Path):
        sm = ScreenshotManager(mock_page, output_dir=str(tmp_path))
        path = await sm.capture("test.png")
        assert "test.png" in path
        mock_page.screenshot.assert_called_with(path=str(tmp_path / "test.png"), full_page=True)

    @pytest.mark.asyncio
    async def test_capture_visible(self, mock_page, tmp_path: Path):
        sm = ScreenshotManager(mock_page, output_dir=str(tmp_path))
        await sm.capture_visible("visible.png")
        mock_page.screenshot.assert_called_with(path=str(tmp_path / "visible.png"), full_page=False)

    @pytest.mark.asyncio
    async def test_capture_element_not_found(self, mock_page):
        mock_page.query_selector = AsyncMock(return_value=None)
        sm = ScreenshotManager(mock_page)
        with pytest.raises(ValueError):
            await sm.capture_element("#missing")

    def test_compare_identical(self, tmp_path: Path):
        p = str(tmp_path / "a.png")
        Path(p).write_text("same content")
        sm = ScreenshotManager(MagicMock())
        diff = sm.compare(p, p)
        assert diff == 0.0

    def test_compare_different(self, tmp_path: Path):
        p1 = str(tmp_path / "a.png")
        p2 = str(tmp_path / "b.png")
        Path(p1).write_text("content a")
        Path(p2).write_text("content b")
        sm = ScreenshotManager(MagicMock())
        diff = sm.compare(p1, p2)
        assert diff > 0.0

    def test_history(self):
        sm = ScreenshotManager(MagicMock())
        assert len(sm.get_history()) == 0

    def test_clear_history(self):
        sm = ScreenshotManager(MagicMock())
        sm._history.append("entry")  # pyright: ignore[reportArgumentType]
        sm.clear_history()
        assert len(sm.get_history()) == 0


@pytest.mark.asyncio
class TestDOMInteraction:
    async def test_get_text_content(self, mock_page):
        mock_page.evaluate = AsyncMock(return_value="Hello World")
        dom = DOMInteraction(mock_page)
        result = await dom.get_text_content("#el")
        assert result == "Hello World"

    async def test_get_value(self, mock_page):
        mock_page.evaluate = AsyncMock(return_value="user input")
        dom = DOMInteraction(mock_page)
        result = await dom.get_value("#input")
        assert result == "user input"

    async def test_is_visible(self, mock_page):
        mock_page.evaluate = AsyncMock(return_value=True)
        dom = DOMInteraction(mock_page)
        assert await dom.is_visible("#el")

    async def test_get_attributes(self, mock_page):
        mock_page.evaluate = AsyncMock(return_value={"class": "btn", "id": "submit"})
        dom = DOMInteraction(mock_page)
        attrs = await dom.get_attributes("#el")
        assert attrs["class"] == "btn"

    async def test_get_dimensions(self, mock_page):
        mock_page.evaluate = AsyncMock(return_value={"x": 0, "y": 0, "width": 100, "height": 50})
        dom = DOMInteraction(mock_page)
        dims = await dom.get_dimensions("#el")
        assert dims["width"] == 100

    async def test_query_all(self, mock_page):
        mock_page.evaluate = AsyncMock(return_value=[{"tagName": "DIV"}, {"tagName": "SPAN"}])
        dom = DOMInteraction(mock_page)
        results = await dom.query_all("div")
        assert len(results) == 2

    async def test_wait_for_element(self, mock_page):
        dom = DOMInteraction(mock_page)
        assert await dom.wait_for_element("#btn")

    async def test_wait_for_element_fail(self, mock_page):
        mock_page.wait_for_selector = AsyncMock(side_effect=Exception("timeout"))
        dom = DOMInteraction(mock_page)
        assert not await dom.wait_for_element("#missing", timeout=100)

    async def test_get_children(self, mock_page):
        mock_page.evaluate = AsyncMock(return_value=[{"tag": "li"}, {"tag": "li"}])
        dom = DOMInteraction(mock_page)
        children = await dom.get_children("ul")
        assert len(children) == 2

    async def test_get_parent(self, mock_page):
        mock_page.evaluate = AsyncMock(return_value={"tag": "div", "id": "container"})
        dom = DOMInteraction(mock_page)
        parent = await dom.get_parent("#child")
        assert parent is not None
        assert parent["tag"] == "div"

    async def test_focus_and_blur(self, mock_page):
        dom = DOMInteraction(mock_page)
        await dom.focus("#input")
        await dom.blur("#input")
