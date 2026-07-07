from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest

from core.browser.finder import ElementFinder
from core.browser.monitor import ConsoleEntry, PageMonitor, PerformanceMetrics
from core.browser.network import NetworkInterceptor, RequestInfo, ResponseInfo
from core.browser.page import PageInteractor, ScrollDirection, WaitStrategy
from core.browser.session import Cookie, SessionManager


class AsyncPageMock:
    """Mock that returns the same AsyncMock per attribute (preserving call tracking)."""
    def __init__(self):
        self._mocks: dict[str, AsyncMock] = {}
        self.context = MagicMock()
        self.keyboard = MagicMock()
        self.url = "https://example.com"

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self._mocks:
            self._mocks[name] = AsyncMock()
        return self._mocks[name]


@pytest.fixture
def mock_page():
    return AsyncPageMock()


class TestPageInteractor:
    def test_init(self, mock_page):
        pi = PageInteractor(mock_page)
        assert pi._page is mock_page

    @pytest.mark.asyncio
    async def test_wait_visible(self, mock_page):
        pi = PageInteractor(mock_page)
        result = await pi.wait(WaitStrategy.VISIBLE, "#button")
        assert result
        mock_page.wait_for_selector.assert_called_with("#button", state="visible", timeout=5000)

    @pytest.mark.asyncio
    async def test_wait_timeout(self, mock_page):
        mock_page.wait_for_selector.side_effect = Exception("timeout")
        pi = PageInteractor(mock_page)
        result = await pi.wait(WaitStrategy.VISIBLE, "#btn", timeout=1000)
        assert not result

    @pytest.mark.asyncio
    async def test_scroll_down(self, mock_page):
        pi = PageInteractor(mock_page)
        await pi.scroll(ScrollDirection.DOWN, 500)
        mock_page.evaluate.assert_called_with("window.scrollBy(0, 500)")

    @pytest.mark.asyncio
    async def test_scroll_top(self, mock_page):
        pi = PageInteractor(mock_page)
        await pi.scroll("top")
        mock_page.evaluate.assert_called_with("window.scrollBy(0, -999999)")

    @pytest.mark.asyncio
    async def test_hover(self, mock_page):
        pi = PageInteractor(mock_page)
        await pi.hover("#btn")
        mock_page.hover.assert_called_with("#btn")

    @pytest.mark.asyncio
    async def test_select_option(self, mock_page):
        pi = PageInteractor(mock_page)
        await pi.select_option("#select", "opt1")
        mock_page.select_option.assert_called_with("#select", "opt1")

    @pytest.mark.asyncio
    async def test_type_text(self, mock_page):
        pi = PageInteractor(mock_page)
        await pi.type_text("#input", "hello", delay=10)
        mock_page.fill.assert_called_with("#input", "")
        mock_page.type.assert_called_with("#input", "hello", delay=10)

    @pytest.mark.asyncio
    async def test_press_key(self, mock_page):
        mock_page.keyboard.press = AsyncMock()
        pi = PageInteractor(mock_page)
        await pi.press_key("Enter")
        mock_page.keyboard.press.assert_called_with("Enter")

    @pytest.mark.asyncio
    async def test_keyboard_type(self, mock_page):
        mock_page.keyboard.type = AsyncMock()
        pi = PageInteractor(mock_page)
        await pi.keyboard_type("hello", delay=5)
        mock_page.keyboard.type.assert_called_with("hello", delay=5)

    @pytest.mark.asyncio
    async def test_switch_to_tab(self, mock_page):
        pages = [MagicMock(), MagicMock(), MagicMock()]
        for p in pages:
            p.bring_to_front = AsyncMock()
        mock_page.context.pages = pages
        pi = PageInteractor(mock_page)
        await pi.switch_to_tab(1)
        pages[1].bring_to_front.assert_called_once()

    @pytest.mark.asyncio
    async def test_open_new_tab(self, mock_page):
        new_page = MagicMock()
        new_page.goto = AsyncMock()
        mock_page.context.new_page = AsyncMock(return_value=new_page)
        pi = PageInteractor(mock_page)
        result = await pi.open_new_tab("https://example.com")
        new_page.goto.assert_called_with("https://example.com")
        assert result is new_page

    @pytest.mark.asyncio
    async def test_close_current_tab(self, mock_page):
        mock_page.context.pages = [MagicMock(), MagicMock()]
        pi = PageInteractor(mock_page)
        await pi.close_current_tab()
        mock_page.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_tabs(self, mock_page):
        p1, p2 = MagicMock(), MagicMock()
        type(p1).url = PropertyMock(return_value="https://a.com")
        type(p2).url = PropertyMock(return_value="https://b.com")
        p1.title = AsyncMock(return_value="Page A")
        p2.title = AsyncMock(return_value="Page B")
        mock_page.context.pages = [p1, p2]
        pi = PageInteractor(mock_page)
        tabs = await pi.get_tabs()
        assert len(tabs) == 2
        assert tabs[0]["url"] == "https://a.com"
        assert tabs[1]["title"] == "Page B"

    @pytest.mark.asyncio
    async def test_inject_css(self, mock_page):
        pi = PageInteractor(mock_page)
        await pi.inject_css("body { color: red; }")
        mock_page.add_style_tag.assert_called_with(content="body { color: red; }")

    @pytest.mark.asyncio
    async def test_inject_js(self, mock_page):
        mock_page.evaluate = AsyncMock(return_value=42)
        pi = PageInteractor(mock_page)
        result = await pi.inject_js("1 + 1")
        assert result == 42

    @pytest.mark.asyncio
    async def test_get_dimensions(self, mock_page):
        mock_page.evaluate = AsyncMock(return_value={
            "viewport": {"width": 1920, "height": 1080},
            "document": {"width": 1920, "height": 3000},
        })
        pi = PageInteractor(mock_page)
        dims = await pi.get_dimensions()
        assert dims["viewport"]["width"] == 1920


class TestSessionManager:
    @pytest.mark.asyncio
    async def test_get_cookies(self, mock_page):
        mock_page.context.cookies = AsyncMock(return_value=[
            {"name": "session", "value": "abc", "domain": ".example.com",
             "path": "/", "expires": -1, "httpOnly": True, "secure": True, "sameSite": "Lax"},
        ])
        sm = SessionManager(mock_page, state_dir="/tmp/sessions")
        cookies = await sm.get_cookies()
        assert len(cookies) == 1
        assert cookies[0].name == "session"
        assert cookies[0].http_only

    @pytest.mark.asyncio
    async def test_set_cookies(self, mock_page):
        mock_page.context.add_cookies = AsyncMock()
        sm = SessionManager(mock_page, state_dir="/tmp/sessions")
        await sm.set_cookies([Cookie(name="test", value="val", domain=".example.com")])
        mock_page.context.add_cookies.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_cookies(self, mock_page):
        mock_page.context.clear_cookies = AsyncMock()
        sm = SessionManager(mock_page, state_dir="/tmp/sessions")
        await sm.clear_cookies()
        mock_page.context.clear_cookies.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_import_cookies(self, mock_page, tmp_path: Path):
        mock_page.context.cookies = AsyncMock(return_value=[
            {"name": "x", "value": "1", "domain": ".ex.com", "path": "/",
             "expires": -1, "httpOnly": False, "secure": False, "sameSite": "Lax"},
        ])
        mock_page.context.add_cookies = AsyncMock()
        sm = SessionManager(mock_page, state_dir="/tmp/sessions")
        export_path = str(tmp_path / "cookies.json")
        await sm.export_cookies(export_path)
        assert Path(export_path).exists()
        count = await sm.import_cookies(export_path)
        assert count == 1

    @pytest.mark.asyncio
    async def test_get_storage(self, mock_page):
        mock_page.evaluate = AsyncMock(side_effect=[
            json.dumps({"key1": "val1"}),
            json.dumps({"sess_key": "sess_val"}),
        ])
        sm = SessionManager(mock_page, state_dir="/tmp/sessions")
        storage = await sm.get_storage()
        assert storage.local["key1"] == "val1"
        assert storage.session["sess_key"] == "sess_val"

    @pytest.mark.asyncio
    async def test_clear_storage(self, mock_page):
        sm = SessionManager(mock_page, state_dir="/tmp/sessions")
        await sm.clear_storage("all")
        assert mock_page.evaluate.call_count == 2

    @pytest.mark.asyncio
    async def test_save_and_restore_session(self, mock_page, tmp_path: Path):
        mock_page.context.cookies = AsyncMock(return_value=[])
        mock_page.evaluate = AsyncMock(return_value=json.dumps({}))
        sm = SessionManager(mock_page, state_dir=str(tmp_path))
        path = await sm.save_session("test_session")
        assert Path(path).exists()
        mock_page.goto = AsyncMock()
        result = await sm.restore_session("test_session")
        assert result

    @pytest.mark.asyncio
    async def test_restore_missing_session(self, tmp_path: Path):
        sm = SessionManager(MagicMock(), state_dir=str(tmp_path))
        result = await sm.restore_session("nonexistent")
        assert not result

    @pytest.mark.asyncio
    async def test_list_sessions(self, tmp_path: Path):
        (tmp_path / "session1.json").write_text("{}")
        (tmp_path / "session2.json").write_text("{}")
        sm = SessionManager(MagicMock(), state_dir=str(tmp_path))
        sessions = await sm.list_sessions()
        assert "session1" in sessions
        assert "session2" in sessions

    @pytest.mark.asyncio
    async def test_delete_session(self, tmp_path: Path):
        (tmp_path / "del_me.json").write_text("{}")
        sm = SessionManager(MagicMock(), state_dir=str(tmp_path))
        assert await sm.delete_session("del_me")
        assert not await sm.delete_session("nonexistent")


class TestNetworkInterceptor:
    @pytest.mark.asyncio
    async def test_start_and_stop(self, mock_page):
        ni = NetworkInterceptor(mock_page)
        await ni.start()
        assert ni._active
        mock_page.route.assert_called_with("**/*", ni._handle_route)
        await ni.stop()
        assert not ni._active

    @pytest.mark.asyncio
    async def test_mock_response(self, mock_page):
        ni = NetworkInterceptor(mock_page)
        ni.mock_response("api/data", body='{"ok": true}', status=200)
        assert len(ni._routes) == 1
        assert ni._routes[0]["body"] == '{"ok": true}'

    @pytest.mark.asyncio
    async def test_mock_json(self, mock_page):
        ni = NetworkInterceptor(mock_page)
        ni.mock_json("/api/users", [{"id": 1}])
        assert json.loads(ni._routes[0]["body"]) == [{"id": 1}]

    @pytest.mark.asyncio
    async def test_block_urls(self, mock_page):
        ni = NetworkInterceptor(mock_page)
        ni.block_urls(["tracker", "analytics"])
        assert "tracker" in ni._blocked_patterns
        assert "analytics" in ni._blocked_patterns

    def _async_route(self):
        route = MagicMock()
        route.abort = AsyncMock()
        route.fulfill = AsyncMock()
        route.fetch = AsyncMock()
        route.request.url = ""
        route.request.method = "GET"
        return route

    @pytest.mark.asyncio
    async def test_handle_route_blocked(self, mock_page):
        ni = NetworkInterceptor(mock_page)
        ni._blocked_patterns.append("blocked")
        route = self._async_route()
        route.request.url = "https://example.com/blocked.js"
        await ni._handle_route(route)
        route.abort.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_route_fulfilled(self, mock_page):
        ni = NetworkInterceptor(mock_page)
        ni.mock_response("api/data", body='{"ok": true}')
        route = self._async_route()
        route.request.url = "https://example.com/api/data"
        await ni._handle_route(route)
        route.fulfill.assert_called_with(
            status=200,
            headers={"Content-Type": "application/json"},
            body='{"ok": true}',
        )

    @pytest.mark.asyncio
    async def test_clear_captures(self, mock_page):
        ni = NetworkInterceptor(mock_page)
        ni._captured_requests.append(RequestInfo(url="http://x.com", method="GET", headers={}))
        ni.clear_captures()
        assert len(ni._captured_requests) == 0

    @pytest.mark.asyncio
    async def test_get_requests_filter(self, mock_page):
        ni = NetworkInterceptor(mock_page)
        ni._captured_requests = [
            RequestInfo(url="http://a.com/api", method="GET", headers={}),
            RequestInfo(url="http://b.com/data", method="POST", headers={}),
        ]
        gets = ni.get_requests(method="GET")
        assert len(gets) == 1
        posts = ni.get_requests(url_pattern="data")
        assert len(posts) == 1

    @pytest.mark.asyncio
    async def test_get_responses_filter(self, mock_page):
        ni = NetworkInterceptor(mock_page)
        ni._captured_responses = [
            ResponseInfo(url="http://x.com", status=200, headers={}),
            ResponseInfo(url="http://x.com", status=404, headers={}),
        ]
        assert len(ni.get_responses(status=404)) == 1

    @pytest.mark.asyncio
    async def test_wait_for_request_timeout(self, mock_page):
        ni = NetworkInterceptor(mock_page)
        result = await ni.wait_for_request("anything", timeout=100)
        assert result is None

    @pytest.mark.asyncio
    async def test_clear_mocks(self, mock_page):
        ni = NetworkInterceptor(mock_page)
        ni.mock_response("/test", body="ok")
        ni.clear_mocks()
        assert len(ni._routes) == 0


class TestElementFinder:
    @pytest.mark.asyncio
    async def test_find_by_text(self, mock_page):
        el = MagicMock()
        el.evaluate = AsyncMock(return_value="#my-element")
        mock_page.query_selector = AsyncMock(return_value=el)
        ef = ElementFinder(mock_page)
        result = await ef.find_by_text("Submit")
        assert result == "#my-element"

    @pytest.mark.asyncio
    async def test_find_by_text_not_found(self, mock_page):
        mock_page.query_selector = AsyncMock(return_value=None)
        ef = ElementFinder(mock_page)
        result = await ef.find_by_text("Nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_find_with_fallback(self, mock_page):
        mock_page.query_selector = AsyncMock(return_value=None)
        ef = ElementFinder(mock_page)
        result = await ef.find(selector="#missing", text="also missing")
        assert result is None

    @pytest.mark.asyncio
    async def test_find_by_xpath(self, mock_page):
        el = MagicMock()
        el.evaluate = AsyncMock(return_value="//div[@id='x']")
        mock_page.query_selector = AsyncMock(return_value=el)
        ef = ElementFinder(mock_page)
        result = await ef.find_by_xpath("//div[@id='x']")
        assert result == "//div[@id='x']"

    @pytest.mark.asyncio
    async def test_wait_for_element(self, mock_page):
        ef = ElementFinder(mock_page)
        result = await ef.wait_for_element("#btn")
        assert result

    @pytest.mark.asyncio
    async def test_wait_for_element_fail(self, mock_page):
        mock_page.wait_for_selector = AsyncMock(side_effect=Exception("not found"))
        ef = ElementFinder(mock_page)
        result = await ef.wait_for_element("#missing", timeout=100)
        assert not result

    @pytest.mark.asyncio
    async def test_is_visible(self, mock_page):
        mock_page.is_visible = AsyncMock(return_value=True)
        ef = ElementFinder(mock_page)
        result = await ef.is_visible("#btn")
        assert result

    @pytest.mark.asyncio
    async def test_is_enabled(self, mock_page):
        mock_page.is_enabled = AsyncMock(return_value=False)
        ef = ElementFinder(mock_page)
        result = await ef.is_enabled("#disabled-btn")
        assert not result

    @pytest.mark.asyncio
    async def test_get_element_info(self, mock_page):
        mock_page.evaluate = AsyncMock(return_value={
            "tag": "button",
            "text": "Click me",
            "attributes": {"class": "btn", "id": "submit"},
            "visible": True,
            "boundingBox": {"x": 0, "y": 0, "width": 100, "height": 50},
        })
        ef = ElementFinder(mock_page)
        info = await ef.get_element_info("#submit")
        assert info is not None
        assert info.tag == "button"
        assert info.visible

    @pytest.mark.asyncio
    async def test_find_all(self, mock_page):
        el1, el2 = MagicMock(), MagicMock()
        mock_page.query_selector_all = AsyncMock(return_value=[el1, el2])
        ef = ElementFinder(mock_page)
        results = await ef.find_all(".item")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_find_by_role(self, mock_page):
        el = MagicMock()
        el.evaluate = AsyncMock(return_value="[role='button']")
        mock_page.query_selector = AsyncMock(return_value=el)
        ef = ElementFinder(mock_page)
        result = await ef.find_by_role("button", "Submit")
        assert result == "[role='button']"


class TestPageMonitor:
    def test_console_entry(self):
        e = ConsoleEntry(level="error", text="fail", url="http://x.com", line=10)
        assert e.level == "error"
        assert e.text == "fail"

    def test_performance_metrics(self):
        m = PerformanceMetrics(dom_content_loaded=100, load=200, dom_nodes=50)
        assert m.dom_content_loaded == 100
        assert m.dom_nodes == 50

    @pytest.mark.asyncio
    async def test_start_stop_console_capture(self, mock_page):
        pm = PageMonitor(mock_page)
        await pm.start_console_capture()
        assert pm._console_handler is not None
        await pm.stop_console_capture()
        assert pm._console_handler is None

    @pytest.mark.asyncio
    async def test_get_console_log(self, mock_page):
        pm = PageMonitor(mock_page)
        pm._console_log = [
            ConsoleEntry(level="info", text="log msg"),
            ConsoleEntry(level="error", text="err msg"),
        ]
        errors = pm.get_console_log("error")
        assert len(errors) == 1
        assert errors[0].text == "err msg"

    def test_has_errors(self):
        pm = PageMonitor(MagicMock())
        assert not pm.has_errors()
        pm._console_log.append(ConsoleEntry(level="error", text="fail"))
        assert pm.has_errors()

    def test_has_warnings(self):
        pm = PageMonitor(MagicMock())
        pm._console_log.append(ConsoleEntry(level="warning", text="warn"))
        assert pm.has_warnings()

    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, mock_page):
        mock_page.evaluate = AsyncMock(side_effect=[
            {"domContentLoaded": 100, "load": 200, "firstPaint": 50, "firstContentfulPaint": 60},
            8000000,
            1500,
        ])
        pm = PageMonitor(mock_page)
        metrics = await pm.get_performance_metrics()
        assert metrics.dom_content_loaded == 100
        assert metrics.load == 200
        assert metrics.js_heap_size == 8000000
        assert metrics.dom_nodes == 1500

    @pytest.mark.asyncio
    async def test_screenshot(self, mock_page, tmp_path: Path):
        pm = PageMonitor(mock_page)
        pm._screenshot_dir = str(tmp_path)
        await pm.screenshot("test_page")
        expected = str(tmp_path / "test_page.png")
        mock_page.screenshot.assert_called_with(path=expected, full_page=True)

    @pytest.mark.asyncio
    async def test_screenshot_diff_first(self, mock_page, tmp_path: Path):
        pm = PageMonitor(mock_page)
        pm._screenshot_dir = str(tmp_path)
        current_path = str(tmp_path / "current.png")
        Path(current_path).write_text("screenshot data")
        mock_page.screenshot = AsyncMock(return_value=current_path)
        result = await pm.screenshot_diff("first")
        assert result is None

    @pytest.mark.asyncio
    async def test_start_stop_mutation_tracking(self, mock_page):
        pm = PageMonitor(mock_page)
        await pm.start_mutation_tracking()
        assert pm._mutation_handler is not None
        await pm.stop_mutation_tracking()
        assert pm._mutation_handler is None

    @pytest.mark.asyncio
    async def test_get_mutation_count(self, mock_page):
        mock_page.evaluate = AsyncMock(return_value=5)
        pm = PageMonitor(mock_page)
        count = await pm.get_mutation_count()
        assert count == 5

    @pytest.mark.asyncio
    async def test_check_accessibility(self, mock_page):
        mock_page.evaluate = AsyncMock(side_effect=[3, 1, 10, 2])
        pm = PageMonitor(mock_page)
        issues = await pm.check_accessibility()
        assert len(issues) == 4
        assert issues[0]["type"] == "missing_alt"
        assert issues[0]["count"] == 3

    def test_clear_console_log(self):
        pm = PageMonitor(MagicMock())
        pm._console_log.append(ConsoleEntry(level="info", text="msg"))
        pm.clear_console_log()
        assert len(pm._console_log) == 0

    @pytest.mark.asyncio
    async def test_performance_metrics_fallback(self, mock_page):
        mock_page.evaluate = AsyncMock(side_effect=Exception("fail"))
        pm = PageMonitor(mock_page)
        metrics = await pm.get_performance_metrics()
        assert metrics.dom_content_loaded == 0.0
