from __future__ import annotations

import argparse
import shlex
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from core.log import log


@dataclass
class CLICommand:
    name: str
    help: str
    handler: Callable[..., Any]
    args: list[dict] = field(default_factory=list)


class CLI:
    """Command-line interface with command registration and execution."""

    def __init__(self, name: str = "lumina"):
        self.name = name
        self._commands: dict[str, CLICommand] = {}
        self._global_args: list[dict] = []

    def command(self, name: str, help: str = "", args: list[dict] | None = None):
        def decorator(func: Callable) -> Callable:
            self._commands[name] = CLICommand(
                name=name,
                help=help or func.__doc__ or "",
                handler=func,
                args=args or [],
            )
            return func

        return decorator

    def register(self, cmd: CLICommand) -> None:
        self._commands[cmd.name] = cmd

    def get_command(self, name: str) -> CLICommand | None:
        return self._commands.get(name)

    def list_commands(self) -> list[CLICommand]:
        return list(self._commands.values())

    def run(self, args: list[str] | None = None) -> int:
        parser = argparse.ArgumentParser(prog=self.name, description="Lumina Developer Platform")
        subparsers = parser.add_subparsers(dest="command", help="Available commands")
        for cmd in self._commands.values():
            sp = subparsers.add_parser(cmd.name, help=cmd.help)
            for arg in cmd.args:
                flags = arg.pop("flags", [])
                sp.add_argument(*flags, **arg)
        try:
            parsed = parser.parse_args(args)
        except SystemExit:
            return 1
        if not parsed.command:
            parser.print_help()
            return 1
        cmd = self._commands.get(parsed.command)
        if not cmd:
            print(f"Unknown command: {parsed.command}")
            return 1
        try:
            kwargs = {k: v for k, v in vars(parsed).items() if k != "command"}
            result = cmd.handler(**kwargs)
            if result is not None:
                print(result)
            return 0
        except Exception as e:
            log.error("Command failed: %s", e)
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def run_string(self, command_line: str) -> int:
        return self.run(shlex.split(command_line))

    def format_table(self, headers: list[str], rows: list[list[str]]) -> str:
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        lines = []
        header = "  ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        lines.append(header)
        lines.append("-" * len(header))
        lines.extend(
            "  ".join(str(c).ljust(col_widths[i]) for i, c in enumerate(row)) for row in rows
        )
        return "\n".join(lines)

    @staticmethod
    def color(text: str, color: str = "blue") -> str:
        colors = {
            "red": "31",
            "green": "32",
            "yellow": "33",
            "blue": "34",
            "magenta": "35",
            "cyan": "36",
        }
        code = colors.get(color, "0")
        return f"\033[{code}m{text}\033[0m"

    @staticmethod
    def success(text: str) -> str:
        return CLI.color(text, "green")

    @staticmethod
    def error(text: str) -> str:
        return CLI.color(text, "red")


# Default CLI instance
cli = CLI()


@cli.command("help", "Show available commands")
def _help():
    cmds = cli.list_commands()
    rows = [[c.name, c.help[:60]] for c in cmds]
    return cli.format_table(["Command", "Description"], rows)


@cli.command("version", "Show version info")
def _version():
    return "Lumina Developer Platform v1.0.0"
