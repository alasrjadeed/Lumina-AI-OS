"""Connectors — OAuth-based external service integrations.

Inspired by OpenJarvis connector system (jarvis connect gdrive).
Supports Gmail, Google Calendar, Google Tasks, and more.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass
class Connector:
    """An external service integration."""

    name: str
    label: str
    description: str
    icon: str = "Globe"
    auth_type: str = "oauth"
    configured: bool = False
    connected: bool = False
    config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "description": self.description,
            "icon": self.icon,
            "auth_type": self.auth_type,
            "configured": self.configured,
            "connected": self.connected,
        }


class ConnectorManager:
    """Manage OAuth-based external service connections."""

    def __init__(self):
        self._connectors: dict[str, Connector] = {}
        self._data_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "connectors_data.json")
        self._init_connectors()
        self._load_state()

    def _init_connectors(self) -> None:
        defaults = [
            Connector("gmail", "Gmail", "Read and send emails", icon="Mail"),
            Connector("google-calendar", "Google Calendar", "View and manage calendar events", icon="Calendar"),
            Connector("google-tasks", "Google Tasks", "Manage task lists", icon="CheckSquare"),
            Connector("google-drive", "Google Drive", "Access and search files", icon="Folder"),
            Connector("outlook", "Outlook", "Microsoft email and calendar", icon="Mail"),
            Connector("slack", "Slack", "Send messages and monitor channels", icon="MessageSquare"),
            Connector("github", "GitHub", "Manage repos, issues, and PRs", icon="GitBranch"),
            Connector("notion", "Notion", "Access notes, databases, and pages", icon="FileText"),
            Connector("linear", "Linear", "Project management and issue tracking", icon="CheckSquare"),
            Connector("spotify", "Spotify", "Control playback and manage playlists", icon="Music"),
        ]
        for c in defaults:
            self._connectors[c.name] = c

    def _load_state(self) -> None:
        if os.path.exists(self._data_file):
            try:
                with open(self._data_file) as f:
                    data = json.load(f)
                for name, state in data.items():
                    if name in self._connectors:
                        self._connectors[name].configured = state.get("configured", False)
                        self._connectors[name].connected = state.get("connected", False)
                        self._connectors[name].config = state.get("config", {})
            except (json.JSONDecodeError, OSError):
                pass

    def _save_state(self) -> None:
        data = {}
        for name, c in self._connectors.items():
            data[name] = {
                "configured": c.configured,
                "connected": c.connected,
                "config": c.config,
            }
        with open(self._data_file, "w") as f:
            json.dump(data, f, indent=2)

    def list_connectors(self) -> list[Connector]:
        return list(self._connectors.values())

    def get_connector(self, name: str) -> Connector | None:
        return self._connectors.get(name)

    def connect(self, name: str, auth_code: str = "") -> bool:
        connector = self._connectors.get(name)
        if not connector:
            return False
        if not auth_code:
            connector.configured = True
            connector.connected = True
            self._save_state()
            return True
        try:
            connector.config["access_token"] = auth_code
            connector.configured = True
            connector.connected = True
            self._save_state()
            return True
        except Exception:
            return False

    def disconnect(self, name: str) -> bool:
        connector = self._connectors.get(name)
        if not connector:
            return False
        connector.configured = False
        connector.connected = False
        connector.config = {}
        self._save_state()
        return True

    async def fetch(self, name: str, endpoint: str) -> dict[str, Any] | None:
        connector = self._connectors.get(name)
        if not connector or not connector.connected:
            return None
        endpoints = {
            "gmail": "https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=5",
            "google-calendar": "https://www.googleapis.com/calendar/v3/calendars/primary/events?maxResults=5",
            "google-tasks": "https://tasks.googleapis.com/tasks/v1/users/@me/lists",
            "google-drive": "https://www.googleapis.com/drive/v3/files?pageSize=10",
            "github": "https://api.github.com/user/repos?per_page=5&sort=updated",
        }
        url = endpoints.get(name)
        if not url:
            return None
        token = connector.config.get("access_token", "")
        if not token:
            return None
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=10)
                if resp.status_code == 200:
                    return resp.json()
                return {"error": f"HTTP {resp.status_code}", "detail": resp.text[:200]}
        except Exception as e:
            return {"error": str(e)}

    def to_dict(self) -> dict[str, Any]:
        return {
            "connectors": [c.to_dict() for c in self._connectors.values()],
            "total": len(self._connectors),
            "connected": sum(1 for c in self._connectors.values() if c.connected),
        }


connector_manager = ConnectorManager()
