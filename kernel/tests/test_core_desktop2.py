from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from core.desktop.chat import ChatHistory, ChatMessage, ChatSession
from core.desktop.logs import LogEntry, LogLevel, LogManager
from core.desktop.plugin_manager import PluginInfo, PluginManager, PluginMetadata
from core.desktop.settings import AppSettings, SettingDefinition
from core.desktop.ui import AppWindow, ThemeManager, WindowState
from core.desktop.ui_notifications import (
    NotificationSeverity,
    UINotification,
    UINotificationManager,
)


class TestThemeManager:
    def test_default_theme(self):
        tm = ThemeManager()
        assert tm.theme == "dark"

    def test_set_theme(self):
        tm = ThemeManager()
        tm.set_theme("light")
        assert tm.theme == "light"

    def test_toggle(self):
        tm = ThemeManager()
        assert tm.toggle() == "light"
        assert tm.toggle() == "dark"

    def test_invalid_theme(self):
        tm = ThemeManager()
        with pytest.raises(ValueError):
            tm.set_theme("invalid")

    def test_on_change_callback(self):
        tm = ThemeManager()
        result = []
        tm.on_change(lambda t: result.append(t))
        tm.set_theme("light")
        assert result == ["light"]

    def test_stylesheet_not_empty(self):
        tm = ThemeManager()
        assert len(tm.get_stylesheet()) > 0
        tm.set_theme("light")
        assert len(tm.get_stylesheet()) > 0


class TestAppWindow:
    def test_default_state(self):
        win = AppWindow()
        assert win.title == "Lumina Desktop"
        assert isinstance(win.state, WindowState)
        assert win.state.width == 1200

    def test_save_load_state(self, tmp_path: Path):
        win = AppWindow()
        win.state.width = 800
        win.state.theme = "light"
        path = str(tmp_path / "state.json")
        win.save_state(path)
        win2 = AppWindow()
        win2.load_state(path)
        assert win2.state.width == 800

    def test_show_returns_false_without_pyside(self):
        win = AppWindow()
        result = win.show()
        assert not result

    def test_initialize_pyside_returns_false_without_pyside(self):
        win = AppWindow()
        assert not win.initialize_pyside()


class TestChatHistory:
    def test_create_session(self, tmp_path: Path):
        ch = ChatHistory(storage_dir=str(tmp_path / "chats"))
        session = ch.create_session("Test Chat")
        assert session.title == "Test Chat"
        assert session.id

    def test_add_message(self, tmp_path: Path):
        ch = ChatHistory(storage_dir=str(tmp_path / "chats"))
        ch.create_session()
        msg = ch.add_message("user", "hello")
        assert msg.role == "user"
        assert msg.content == "hello"

    def test_list_sessions(self, tmp_path: Path):
        ch = ChatHistory(storage_dir=str(tmp_path / "chats"))
        ch.create_session("First")
        ch.create_session("Second")
        assert len(ch.list_sessions()) == 2

    def test_switch_session(self, tmp_path: Path):
        ch = ChatHistory(storage_dir=str(tmp_path / "chats"))
        ch.create_session("S1")
        s2 = ch.create_session("S2")
        assert ch.switch_to(s2.id)
        assert ch.current_session().id == s2.id

    def test_get_messages(self, tmp_path: Path):
        ch = ChatHistory(storage_dir=str(tmp_path / "chats"))
        ch.create_session()
        ch.add_message("user", "hi")
        ch.add_message("assistant", "hello")
        msgs = ch.get_messages()
        assert len(msgs) == 2

    def test_search(self, tmp_path: Path):
        ch = ChatHistory(storage_dir=str(tmp_path / "chats"))
        ch.create_session()
        ch.add_message("user", "what is the weather")
        ch.add_message("assistant", "it is sunny")
        results = ch.search("weather")
        assert len(results) == 1

    def test_delete_session(self, tmp_path: Path):
        ch = ChatHistory(storage_dir=str(tmp_path / "chats"))
        s = ch.create_session()
        assert ch.delete_session(s.id)
        assert not ch.delete_session("nonexistent")

    def test_clear_current(self, tmp_path: Path):
        ch = ChatHistory(storage_dir=str(tmp_path / "chats"))
        ch.create_session()
        ch.add_message("user", "msg")
        ch.clear_current()
        assert len(ch.get_messages()) == 0

    def test_load_all(self, tmp_path: Path):
        ch = ChatHistory(storage_dir=str(tmp_path / "chats"))
        ch.create_session("Loaded")
        path = ch._session_path(ch.current_session().id)
        assert os.path.exists(path)

    def test_chat_message_properties(self):
        msg = ChatMessage(role="user", content="test")
        assert msg.is_user
        assert not msg.is_assistant
        assert msg.formatted_time

    def test_chat_session_properties(self):
        session = ChatSession(id="1", title="Test")
        assert session.message_count == 0
        assert session.last_message is None
        session.messages.append(ChatMessage(role="user", content="hi"))
        assert session.message_count == 1
        assert session.last_message is not None


class TestAppSettings:
    def test_define_and_get(self, tmp_path: Path):
        path = str(tmp_path / "settings.json")
        s = AppSettings(path)
        s.define(SettingDefinition(key="name", label="Name", default="Alice"))
        assert s.get("name") == "Alice"

    def test_set_and_get(self, tmp_path: Path):
        path = str(tmp_path / "settings.json")
        s = AppSettings(path)
        s.define(SettingDefinition(key="volume", label="Volume", type="int", default=50))
        s.set("volume", 75)
        assert s.get("volume") == 75

    def test_set_many(self, tmp_path: Path):
        path = str(tmp_path / "settings.json")
        s = AppSettings(path)
        s.define(SettingDefinition(key="a", label="A", default=1))
        s.define(SettingDefinition(key="b", label="B", default=2))
        s.set_many({"a": 10, "b": 20})
        assert s.get("a") == 10
        assert s.get("b") == 20

    def test_reset(self, tmp_path: Path):
        path = str(tmp_path / "settings.json")
        s = AppSettings(path)
        s.define(SettingDefinition(key="x", label="X", default=100))
        s.set("x", 200)
        s.reset("x")
        assert s.get("x") == 100

    def test_reset_all(self, tmp_path: Path):
        path = str(tmp_path / "settings.json")
        s = AppSettings(path)
        s.define(SettingDefinition(key="a", label="A", default=1))
        s.define(SettingDefinition(key="b", label="B", default=2))
        s.set_many({"a": 99, "b": 88})
        s.reset_all()
        assert s.get("a") == 1
        assert s.get("b") == 2

    def test_categories(self, tmp_path: Path):
        path = str(tmp_path / "settings.json")
        s = AppSettings(path)
        s.define(SettingDefinition(key="k1", label="K1", category="cat1"))
        s.define(SettingDefinition(key="k2", label="K2", category="cat2"))
        assert "cat1" in s.categories()
        assert "cat2" in s.categories()

    def test_get_category(self, tmp_path: Path):
        path = str(tmp_path / "settings.json")
        s = AppSettings(path)
        s.define(SettingDefinition(key="k1", label="K1", category="cat1", default="v1"))
        s.define(SettingDefinition(key="k2", label="K2", category="cat2", default="v2"))
        cat = s.get_category("cat1")
        assert cat["k1"] == "v1"
        assert "k2" not in cat

    def test_on_change(self, tmp_path: Path):
        path = str(tmp_path / "settings.json")
        s = AppSettings(path)
        s.define(SettingDefinition(key="key", label="Key", default="old"))
        result = []
        s.on_change("key", lambda k, v: result.append((k, v)))
        s.set("key", "new")
        assert result == [("key", "new")]

    def test_export_import(self, tmp_path: Path):
        path = str(tmp_path / "settings.json")
        s = AppSettings(path)
        s.define(SettingDefinition(key="k", label="K", default="val"))
        exported = s.export_json(str(tmp_path / "export.json"))
        assert os.path.exists(exported)
        s2 = AppSettings(str(tmp_path / "settings2.json"))
        s2.define(SettingDefinition(key="k", label="K", default=""))
        count = s2.import_json(exported)
        assert count == 1
        assert s2.get("k") == "val"

    def test_default_settings(self, tmp_path: Path):
        path = str(tmp_path / "default.json")
        s = AppSettings.default_settings(path)
        assert s.get("theme") == "dark"
        assert s.get("font_size") == 14
        assert s.get("temperature") == 0.7

    def test_all(self, tmp_path: Path):
        path = str(tmp_path / "settings.json")
        s = AppSettings(path)
        s.define(SettingDefinition(key="k", label="K", default="v"))
        assert s.all() == {"k": "v"}


class TestPluginManager:
    def test_list_plugins_empty(self):
        pm = PluginManager()
        assert pm.list_plugins() == []

    def test_load_nonexistent(self):
        pm = PluginManager()
        assert not pm.load("nonexistent_plugin")

    def test_is_loaded(self):
        pm = PluginManager()
        assert not pm.is_loaded("nonexistent")

    def test_enable_disable(self):
        pm = PluginManager()
        assert not pm.enable("nonexistent")
        assert not pm.disable("nonexistent")

    def test_get_plugin(self):
        pm = PluginManager()
        assert pm.get_plugin("nonexistent") is None

    def test_register_and_trigger_hook(self):
        pm = PluginManager()
        results = []
        pm.register_hook("test_hook", lambda x: results.append(x))
        pm.trigger_hook("test_hook", "data")
        assert "data" in results

    def test_trigger_hook_no_registrations(self):
        pm = PluginManager()
        assert pm.trigger_hook("unregistered") == []

    def test_list_enabled_only(self):
        pm = PluginManager()
        pm._plugins["a"] = PluginInfo(metadata=PluginMetadata(name="a"), enabled=True)
        pm._plugins["b"] = PluginInfo(metadata=PluginMetadata(name="b"), enabled=False)
        enabled = pm.list_plugins(enabled_only=True)
        assert len(enabled) == 1
        assert enabled[0].metadata.name == "a"

    def test_unload_nonexistent(self):
        pm = PluginManager()
        assert not pm.unload("nonexistent")

    def test_unload_all_empty(self):
        pm = PluginManager()
        assert pm.unload_all() == 0

    def test_load_all_empty_dir(self, tmp_path: Path):
        pm = PluginManager(plugin_dirs=[str(tmp_path / "empty")])
        assert pm.load_all() == 0


class TestUINotificationManager:
    def test_notify(self):
        nm = UINotificationManager()
        n = nm.notify("Title", "Message")
        assert n.title == "Title"
        assert n.message == "Message"
        assert n.severity == NotificationSeverity.INFO

    def test_notify_with_string_severity(self):
        nm = UINotificationManager()
        n = nm.notify("T", "M", severity="error")
        assert n.severity == NotificationSeverity.ERROR

    def test_get_active(self):
        nm = UINotificationManager()
        nm.notify("T", "M")
        nm.notify("T2", "M2")
        assert len(nm.get_active()) == 2

    def test_dismiss(self):
        nm = UINotificationManager()
        n = nm.notify("T", "M")
        assert nm.dismiss(n.id)
        assert not nm.dismiss("nonexistent")

    def test_dismiss_all(self):
        nm = UINotificationManager()
        nm.notify("T1", "M1")
        nm.notify("T2", "M2")
        assert nm.dismiss_all() == 2

    def test_get_unread_count(self):
        nm = UINotificationManager()
        nm.notify("T", "M")
        assert nm.get_unread_count() == 1

    def test_expired_notification(self):
        nm = UINotificationManager()
        n = nm.notify("T", "M", timeout=0.001)
        time.sleep(0.005)
        assert n.is_expired
        assert len(nm.get_active()) == 0

    def test_clear_expired(self):
        nm = UINotificationManager()
        nm.notify("T", "M", timeout=0.001)
        time.sleep(0.005)
        assert nm.clear_expired() >= 1

    def test_clear_all(self):
        nm = UINotificationManager()
        nm.notify("T", "M")
        nm.clear_all()
        assert len(nm.get_all()) == 0

    def test_severity_helpers(self):
        nm = UINotificationManager()
        assert nm.info("I", "Info").severity == NotificationSeverity.INFO
        assert nm.success("S", "Ok").severity == NotificationSeverity.SUCCESS
        assert nm.warning("W", "Careful").severity == NotificationSeverity.WARNING
        assert nm.error("E", "Fail").severity == NotificationSeverity.ERROR

    def test_on_show_callback(self):
        nm = UINotificationManager()
        result = []
        nm.on_show(lambda n: result.append(n.id))
        n = nm.notify("T", "M")
        assert result == [n.id]

    def test_trim_excess(self):
        nm = UINotificationManager(max_visible=3)
        for i in range(10):
            nm.notify(f"T{i}", f"M{i}")
        assert len(nm.get_all()) <= 6

    def test_icon_lookup(self):
        assert UINotification(id="1", title="T", message="M",
            severity=NotificationSeverity.INFO).icon == "ℹ"
        assert UINotification(id="2", title="T", message="M",
            severity=NotificationSeverity.ERROR).icon == "✗"


class TestLogManager:
    def test_log_basic(self):
        lm = LogManager()
        entry = lm.log(LogLevel.INFO, "test message")
        assert entry.level == LogLevel.INFO
        assert entry.message == "test message"

    def test_log_with_string_level(self):
        lm = LogManager()
        entry = lm.log("error", "error message")
        assert entry.level == LogLevel.ERROR

    def test_convenience_methods(self):
        lm = LogManager()
        lm.debug("debug")
        lm.info("info")
        lm.warning("warn")
        lm.error("err")
        lm.critical("crit")
        assert lm.count() == 5

    def test_get_recent(self):
        lm = LogManager()
        lm.info("first")
        lm.info("second")
        recent = lm.get_recent(2)
        assert len(recent) == 2
        assert recent[0].message == "second"

    def test_get_by_level(self):
        lm = LogManager()
        lm.info("info msg")
        lm.error("error msg")
        errors = lm.get_by_level(LogLevel.ERROR)
        assert len(errors) == 1
        assert errors[0].message == "error msg"

    def test_get_with_source_filter(self):
        lm = LogManager()
        lm.info("msg1", source="module_a")
        lm.info("msg2", source="module_b")
        results = lm.get(source="module_a")
        assert len(results) == 1

    def test_search(self):
        lm = LogManager()
        lm.info("connection established")
        lm.error("connection failed")
        results = lm.search("failed")
        assert len(results) == 1

    def test_get_errors(self):
        lm = LogManager()
        lm.info("info")
        lm.error("err1")
        lm.critical("crit1")
        errors = lm.get_errors()
        assert len(errors) == 2

    def test_count_by_level(self):
        lm = LogManager()
        lm.info("i1")
        lm.info("i2")
        lm.error("e1")
        assert lm.count(LogLevel.INFO) == 2
        assert lm.count(LogLevel.ERROR) == 1

    def test_clear(self):
        lm = LogManager()
        lm.info("test")
        lm.clear()
        assert lm.count() == 0

    def test_export_json(self, tmp_path: Path):
        lm = LogManager()
        lm.info("export test")
        path = lm.export_json(str(tmp_path / "log.json"))
        assert os.path.exists(path)
        with open(path) as f:
            data = json.load(f)
        assert len(data) >= 1

    def test_export_text(self, tmp_path: Path):
        lm = LogManager()
        lm.info("text export")
        path = lm.export_text(str(tmp_path / "log.txt"))
        assert os.path.exists(path)

    def test_save_and_load(self, tmp_path: Path):
        path = str(tmp_path / "persist.json")
        lm = LogManager(storage_path=path)
        lm.info("persistent log")
        lm.save()
        lm2 = LogManager(storage_path=path)
        count = lm2.load()
        assert count == 1
        assert lm2.get_recent(1)[0].message == "persistent log"

    def test_log_entry_to_dict(self):
        entry = LogEntry(level=LogLevel.INFO, message="test")
        d = entry.to_dict()
        assert d["level"] == "info"
        assert d["message"] == "test"
