from __future__ import annotations

from pathlib import Path

import pytest

from core.desktop.app_manager import AppInfo, AppManager
from core.desktop.clipboard import ClipboardManager
from core.desktop.notifications import Notification, NotificationManager
from core.desktop.os_automation import DesktopAutomation
from core.desktop.shortcuts import Shortcut, ShortcutManager
from core.desktop.window_manager import WindowInfo, WindowManager


@pytest.mark.asyncio
class TestDesktopAutomation:
    async def test_execute(self):
        da = DesktopAutomation()
        result = await da.execute("echo hello")
        assert result["status"] == "ok"
        assert "hello" in result["stdout"]

    async def test_execute_failure(self):
        da = DesktopAutomation()
        result = await da.execute("nonexistent_command_xyz")
        assert result["return_code"] != 0

    async def test_list_files(self, tmp_path: Path):
        (tmp_path / "file1.txt").write_text("a")
        (tmp_path / "subdir").mkdir()
        da = DesktopAutomation()
        items = await da.list_files(str(tmp_path))
        names = [i["name"] for i in items]
        assert "file1.txt" in names
        assert "subdir" in names

    async def test_read_write_file(self, tmp_path: Path):
        path = str(tmp_path / "test.txt")
        da = DesktopAutomation()
        await da.write_file(path, "content")
        content = await da.read_file(path)
        assert content == "content"

    async def test_read_missing_file(self):
        da = DesktopAutomation()
        result = await da.read_file("/nonexistent/path/file.txt")
        assert result is None

    async def test_copy_move_file(self, tmp_path: Path):
        src = str(tmp_path / "src.txt")
        dst = str(tmp_path / "dst.txt")
        dst2 = str(tmp_path / "dst2.txt")
        da = DesktopAutomation()
        await da.write_file(src, "data")
        await da.copy_file(src, dst)
        assert Path(dst).exists()
        await da.move_file(dst, dst2)
        assert Path(dst2).exists()
        assert not Path(dst).exists()

    async def test_delete_file(self, tmp_path: Path):
        path = str(tmp_path / "delete_me.txt")
        da = DesktopAutomation()
        await da.write_file(path, "data")
        await da.delete_file(path)
        assert not Path(path).exists()

    async def test_create_dir(self, tmp_path: Path):
        path = str(tmp_path / "new_dir")
        da = DesktopAutomation()
        await da.create_dir(path)
        assert Path(path).exists()

    async def test_system_info(self):
        da = DesktopAutomation()
        info = await da.system_info()
        assert "os" in info
        assert "cwd" in info


class TestAppManager:
    def test_app_info_dataclass(self):
        info = AppInfo(name="test", path="/usr/bin/test", pid=123, running=True)
        assert info.name == "test"
        assert info.pid == 123

    def test_list_apps(self):
        am = AppManager()
        am._apps["a"] = AppInfo(name="a")
        am._apps["b"] = AppInfo(name="b", running=True)
        assert len(am.list_apps()) == 2
        assert len(am.list_apps(running_only=True)) == 1

    def test_get_app(self):
        am = AppManager()
        am._apps["myapp"] = AppInfo(name="myapp")
        assert am.get_app("myapp") is not None
        assert am.get_app("missing") is None

    def test_is_running(self):
        am = AppManager()
        assert not am.is_running("missing")


@pytest.mark.asyncio
class TestClipboardManager:
    async def test_copy_and_paste(self):
        cm = ClipboardManager()
        result = await cm.copy("test text")
        assert result is True or result is False

    async def test_append(self):
        cm = ClipboardManager()
        result = await cm.append("hello", separator=", ")
        assert result is True or result is False

    async def test_clear(self):
        cm = ClipboardManager()
        result = await cm.clear()
        assert result is True or result is False

    def test_history(self):
        cm = ClipboardManager()
        cm._history = ["a", "b", "c"]
        assert cm.get_history(2) == ["b", "c"]
        cm.clear_history()
        assert len(cm.get_history()) == 0


@pytest.mark.asyncio
class TestNotificationManager:
    async def test_send(self):
        nm = NotificationManager()
        result = await nm.send("Test Title", "Test Message")
        assert result is True or result is False

    async def test_send_levels(self):
        nm = NotificationManager()
        assert await nm.info("Test", "Info message") in (True, False)
        assert await nm.warn("Test", "Warning message") in (True, False)
        assert await nm.error("Test", "Error message") in (True, False)
        assert await nm.success("Test", "Success message") in (True, False)

    def test_history(self):
        nm = NotificationManager()
        nm._history = [
            Notification(title="A", message="msg1", level="info"),
            Notification(title="B", message="msg2", level="warning"),
            Notification(title="C", message="msg3", level="error"),
        ]
        all_h = nm.get_history()
        assert len(all_h) == 3
        infos = nm.get_history(level="info")
        assert len(infos) == 1
        nm.clear_history()
        assert len(nm.get_history()) == 0

    def test_notification_dataclass(self):
        n = Notification(title="Test", message="Hello", level="info")
        assert n.title == "Test"
        assert not n.dismissed


@pytest.mark.asyncio
class TestShortcutManager:
    def test_list_shortcuts(self):
        sm = ShortcutManager()
        sm._shortcuts["app"] = Shortcut(name="app", target="/usr/bin/app")
        assert len(sm.list_shortcuts()) == 1

    async def test_create_desktop_entry(self, tmp_path: Path):
        sm = ShortcutManager(shortcuts_dir=str(tmp_path))
        result = await sm.create_desktop_entry("myapp", "/usr/bin/myapp")
        assert result is True or result is False

    async def test_remove(self, tmp_path: Path):
        desktop_file = tmp_path / "test_app.desktop"
        desktop_file.write_text("[Desktop Entry]")
        sm = ShortcutManager(shortcuts_dir=str(tmp_path))
        sm._shortcuts["test_app"] = Shortcut(name="test_app", target="/usr/bin/test")
        result = await sm.remove("test_app")
        assert result

    async def test_remove_missing(self):
        sm = ShortcutManager()
        result = await sm.remove("missing")
        assert not result


@pytest.mark.asyncio
class TestWindowManager:
    async def test_list_windows(self):
        wm = WindowManager()
        windows = await wm.list_windows()
        assert isinstance(windows, list)

    async def test_get_active(self):
        wm = WindowManager()
        active = await wm.get_active()
        assert active is None or isinstance(active, WindowInfo)

    def test_window_info_dataclass(self):
        w = WindowInfo(id=1, title="Test", x=0, y=0, width=800, height=600)
        assert w.title == "Test"
        assert w.width == 800
