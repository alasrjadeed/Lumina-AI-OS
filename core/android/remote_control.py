from __future__ import annotations

import json
import socket
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from core.android.client import AndroidClient
from core.log import log


class CommandType(Enum):
    TAP = "tap"
    SWIPE = "swipe"
    TEXT = "text"
    KEYEVENT = "keyevent"
    SCREENSHOT = "screenshot"
    SHELL = "shell"
    OPEN_APP = "open_app"
    CLOSE_APP = "close_app"
    GO_BACK = "go_back"
    GO_HOME = "go_home"
    WAKE = "wake"
    LOCK = "lock"
    INFO = "info"
    BATTERY = "battery"
    CLIPBOARD_GET = "clipboard_get"
    CLIPBOARD_SET = "clipboard_set"
    BATCH = "batch"
    PING = "ping"


@dataclass
class RemoteCommand:
    type: CommandType
    params: dict[str, Any] = field(default_factory=dict)
    id: str = ""

    def to_dict(self) -> dict:
        return {"type": self.type.value, "params": self.params, "id": self.id}

    @staticmethod
    def from_dict(data: dict) -> RemoteCommand:
        return RemoteCommand(
            type=CommandType(data["type"]),
            params=data.get("params", {}),
            id=data.get("id", ""),
        )


@dataclass
class CommandResult:
    success: bool
    data: Any = None
    error: str = ""
    command_id: str = ""


CommandHandler = Callable[[RemoteCommand], CommandResult]


class RemoteControl:
    """Remote control server/client for Android device automation."""

    def __init__(self, client: AndroidClient | None = None):
        self.client = client or AndroidClient()
        self._handlers: dict[CommandType, CommandHandler] = {}
        self._server_socket: socket.socket | None = None
        self._running = False
        self._thread: threading.Thread | None = None
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        self.register(CommandType.TAP, lambda c: CommandResult(
            success=True,
            data=self.client.device.input_tap(
                c.params.get("x", 0), c.params.get("y", 0),
            ),
        ))
        self.register(CommandType.SWIPE, lambda c: CommandResult(
            success=True,
            data=self.client.device.swipe(
                c.params.get("x1", 0), c.params.get("y1", 0),
                c.params.get("x2", 0), c.params.get("y2", 0),
                c.params.get("duration", 300),
            ),
        ))
        self.register(CommandType.TEXT, lambda c: CommandResult(
            success=True,
            data=self.client.device.input_text(c.params.get("text", "")),
        ))
        self.register(CommandType.KEYEVENT, lambda c: CommandResult(
            success=True,
            data=self.client.device.input_keyevent(c.params.get("keycode", 0)),
        ))
        self.register(CommandType.SCREENSHOT, lambda c: CommandResult(
            success=True,
            data=self.client.take_screenshot(c.params.get("path", "screenshot.png")),
        ))
        self.register(CommandType.SHELL, lambda c: CommandResult(
            success=True,
            data=self.client.device.shell(c.params.get("command", "")),
        ))
        self.register(CommandType.OPEN_APP, lambda c: CommandResult(
            success=self.client.app_launch(
                c.params.get("package", ""), c.params.get("activity", ""),
            ),
        ))
        self.register(CommandType.CLOSE_APP, lambda c: CommandResult(
            success=True,
            data=self.client.app_force_stop(c.params.get("package", "")),
        ))
        self.register(CommandType.GO_BACK, lambda c: CommandResult(
            success=True, data=self.client.device.press_back(),
        ))
        self.register(CommandType.GO_HOME, lambda c: CommandResult(
            success=True, data=self.client.device.press_home(),
        ))
        self.register(CommandType.WAKE, lambda c: CommandResult(
            success=True, data=self.client.wake(),
        ))
        self.register(CommandType.LOCK, lambda c: CommandResult(
            success=True, data=self.client.lock(),
        ))
        self.register(CommandType.INFO, lambda c: CommandResult(
            success=True, data=self.client.device.get_device_info(),
        ))
        self.register(CommandType.BATTERY, lambda c: CommandResult(
            success=True, data={"level": self.client.battery_level()},
        ))
        self.register(CommandType.PING, lambda c: CommandResult(
            success=True, data={"pong": True, "timestamp": time.time()},
        ))

    def register(self, command_type: CommandType, handler: CommandHandler) -> None:
        self._handlers[command_type] = handler

    def execute(self, command: RemoteCommand) -> CommandResult:
        handler = self._handlers.get(command.type)
        if not handler:
            return CommandResult(success=False, error=f"No handler for {command.type}")
        try:
            result = handler(command)
            result.command_id = command.id
            return result
        except Exception as e:
            return CommandResult(success=False, error=str(e), command_id=command.id)

    def execute_batch(self, commands: list[RemoteCommand]) -> list[CommandResult]:
        return [self.execute(cmd) for cmd in commands]

    def _parse_command(self, data: dict) -> RemoteCommand | None:
        try:
            return RemoteCommand.from_dict(data)
        except (ValueError, KeyError):
            return None

    def execute_json(self, json_str: str) -> str:
        data = json.loads(json_str)
        if isinstance(data, list):
            commands = []
            for d in data:
                cmd = self._parse_command(d)
                if cmd:
                    commands.append(cmd)
                else:
                    return json.dumps([
                        {"success": False, "error": f"Unknown type: {d.get('type')}"},
                    ])
            results = self.execute_batch(commands)
        else:
            cmd = self._parse_command(data)
            if not cmd:
                return json.dumps(
                    [{"success": False, "error": f"Unknown type: {data.get('type')}"}]
                )
            results = [self.execute(cmd)]
        return json.dumps([{"success": r.success, "data": r.data, "error": r.error,
                            "command_id": r.command_id} for r in results])

    # ── TCP Server ──

    def start_server(self, host: str = "0.0.0.0", port: int = 8741) -> bool:
        if self._running:
            return False
        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.bind((host, port))
            self._server_socket.listen(5)
            self._server_socket.settimeout(1.0)
            self._running = True
            self._thread = threading.Thread(target=self._server_loop, daemon=True)
            self._thread.start()
            log.info("Remote control server started on %s:%d", host, port)
            return True
        except Exception as e:
            log.error("Failed to start server: %s", e)
            return False

    def stop_server(self) -> None:
        self._running = False
        if self._server_socket:
            self._server_socket.close()
            self._server_socket = None
        log.info("Remote control server stopped")

    def _server_loop(self) -> None:
        while self._running:
            try:
                client, addr = self._server_socket.accept()
                t = threading.Thread(
                    target=self._handle_client, args=(client, addr), daemon=True,
                )
                t.start()
            except TimeoutError:
                continue
            except Exception:
                break

    def _handle_client(self, client: socket.socket, addr: tuple) -> None:
        log.info("Client connected: %s", addr)
        try:
            client.settimeout(30)
            data = b""
            while self._running:
                chunk = client.recv(4096)
                if not chunk:
                    break
                data += chunk
                try:
                    response = self.execute_json(data.decode("utf-8"))
                    client.sendall(response.encode("utf-8"))
                    data = b""
                except (json.JSONDecodeError, UnicodeDecodeError):
                    if len(data) > 65536:
                        break
                    continue
        except Exception:
            pass
        finally:
            client.close()
            log.info("Client disconnected: %s", addr)
