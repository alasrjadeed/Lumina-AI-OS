from __future__ import annotations

import json
from unittest.mock import patch

from core.android.client import AndroidClient, AppInfo, ScreenInfo
from core.android.notifications import AndroidNotification, AndroidNotificationManager
from core.android.remote_control import CommandResult, CommandType, RemoteCommand, RemoteControl
from core.android.voice import AndroidVoiceInterface, VoiceCaptureResult


class TestAppInfo:
    def test_dataclass(self):
        info = AppInfo(package="com.test.app", name="Test", version="1.0", pid=123, running=True)
        assert info.package == "com.test.app"
        assert info.running


class TestScreenInfo:
    def test_dataclass(self):
        si = ScreenInfo(width=1080, height=1920, density=420, rotation=0)
        assert si.width == 1080
        assert si.density == 420


class TestAndroidClient:
    def test_init(self):
        client = AndroidClient()
        assert client.device is not None

    def test_connect_without_adb(self):
        client = AndroidClient()
        result = client.connect()
        assert not result

    def test_is_connected_false_by_default(self):
        client = AndroidClient()
        assert not client.is_connected

    def test_app_info_dataclass(self):
        info = AppInfo(package="com.test", version="2.0", pid=456, running=True)
        assert info.package == "com.test"
        assert info.pid == 456


class TestAndroidNotification:
    def test_dataclass(self):
        n = AndroidNotification(package="com.test", title="Hello", text="World")
        assert n.package == "com.test"
        assert n.title == "Hello"
        assert n.text == "World"

    def test_timestamp_set(self):
        n = AndroidNotification(package="pkg", title="T", text="M")
        assert n.timestamp > 0


class TestAndroidNotificationManager:
    def test_init(self):
        nm = AndroidNotificationManager()
        assert nm.count() == 0

    def test_start_stop_monitoring(self):
        nm = AndroidNotificationManager()
        nm.start_monitoring()
        assert nm._monitoring
        nm.stop_monitoring()
        assert not nm._monitoring

    def test_get_history_empty(self):
        nm = AndroidNotificationManager()
        assert nm.get_history() == []

    def test_get_by_package_empty(self):
        nm = AndroidNotificationManager()
        assert nm.get_by_package("com.test") == []

    def test_clear_history(self):
        nm = AndroidNotificationManager()
        nm._notifications.append(AndroidNotification(package="pkg", title="T", text="M"))
        nm.clear_history()
        assert nm.count() == 0

    def test_send_adds_to_history(self):
        nm = AndroidNotificationManager()
        with patch.object(nm.device, "shell", return_value=""):
            result = nm.send("Title", "Message")
            assert result
            assert nm.count() == 1

    def test_send_failure(self):
        nm = AndroidNotificationManager()
        with patch.object(nm.device, "shell", side_effect=Exception("no device")):
            result = nm.send("T", "M")
            assert not result


class TestRemoteCommand:
    def test_command_type_values(self):
        assert CommandType.TAP.value == "tap"
        assert CommandType.PING.value == "ping"
        assert CommandType.BATCH.value == "batch"

    def test_to_from_dict(self):
        cmd = RemoteCommand(type=CommandType.TAP, params={"x": 100, "y": 200}, id="cmd1")
        d = cmd.to_dict()
        assert d["type"] == "tap"
        assert d["params"]["x"] == 100
        cmd2 = RemoteCommand.from_dict(d)
        assert cmd2.type == CommandType.TAP
        assert cmd2.params["y"] == 200
        assert cmd2.id == "cmd1"

    def test_command_result(self):
        r = CommandResult(success=True, data="ok", command_id="c1")
        assert r.success
        assert r.data == "ok"
        assert r.command_id == "c1"


class TestRemoteControl:
    def test_init(self):
        rc = RemoteControl()
        assert rc.client is not None

    def test_register_handler(self):
        rc = RemoteControl()
        rc.register(CommandType.PING, lambda c: CommandResult(success=True))
        assert CommandType.PING in rc._handlers

    def test_execute_registered(self):
        rc = RemoteControl()
        result = rc.execute(RemoteCommand(type=CommandType.PING))
        assert result.success

    def test_execute_unregistered(self):
        rc = RemoteControl()
        result = rc.execute(RemoteCommand(type=CommandType.GO_HOME))
        assert result.success

    def test_execute_batch(self):
        rc = RemoteControl()
        results = rc.execute_batch([
            RemoteCommand(type=CommandType.PING),
            RemoteCommand(type=CommandType.PING),
        ])
        assert len(results) == 2
        assert all(r.success for r in results)

    def test_execute_json_single(self):
        rc = RemoteControl()
        response = rc.execute_json('{"type": "ping", "params": {}, "id": "1"}')
        data = json.loads(response)
        assert data[0]["success"]

    def test_execute_json_batch(self):
        rc = RemoteControl()
        response = rc.execute_json('[{"type": "ping"}, {"type": "info"}]')
        data = json.loads(response)
        assert len(data) == 2
        assert all(d["success"] for d in data)

    def test_execute_json_error(self):
        rc = RemoteControl()
        response = rc.execute_json('{"type": "nonexistent", "params": {}}')
        data = json.loads(response)
        assert not data[0]["success"]

    def test_start_stop_server(self):
        rc = RemoteControl()
        result = rc.start_server(host="127.0.0.1", port=0)
        assert result
        rc.stop_server()
        assert not rc._running

    def test_start_server_twice(self):
        rc = RemoteControl()
        rc.start_server(host="127.0.0.1", port=0)
        result = rc.start_server(host="127.0.0.1", port=0)
        assert not result
        rc.stop_server()


class TestAndroidVoiceInterface:
    def test_init(self):
        vi = AndroidVoiceInterface()
        assert vi.device is not None

    def test_capture_result_dataclass(self):
        r = VoiceCaptureResult(
            audio_path="/tmp/test.raw", duration_ms=5000,
            text="hello", success=True,
        )
        assert r.audio_path == "/tmp/test.raw"
        assert r.text == "hello"
        assert r.success

    def test_listen_for_command_without_adb(self):
        vi = AndroidVoiceInterface()
        result = vi.listen_for_command(timeout=1)
        assert result == ""

    def test_listen_for_wake_word_timeout(self):
        vi = AndroidVoiceInterface()
        result = vi.listen_for_wake_word(wake_word="lumina", timeout=1)
        assert not result

    def test_speak_without_provider(self):
        vi = AndroidVoiceInterface()
        result = vi.speak("hello")
        assert result

    def test_speak_file_missing(self):
        vi = AndroidVoiceInterface()
        with patch.object(vi.device, "push", side_effect=Exception("no device")):
            result = vi.speak_file("/nonexistent/file.mp3")
            assert not result
