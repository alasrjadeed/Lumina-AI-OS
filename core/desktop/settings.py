from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SettingDefinition:
    key: str
    label: str
    type: str = "string"
    default: Any = ""
    description: str = ""
    options: list[str] = field(default_factory=list)
    category: str = "general"
    min: float | None = None
    max: float | None = None


class AppSettings:
    """Hierarchical application settings with change listeners."""

    def __init__(self, path: str = "lumina_settings.json"):
        self.path = path
        self._data: dict[str, Any] = {}
        self._definitions: dict[str, SettingDefinition] = {}
        self._listeners: dict[str, list[Callable[[str, Any], None]]] = {}
        self._load()

    def define(self, definition: SettingDefinition) -> None:
        self._definitions[definition.key] = definition
        if definition.key not in self._data:
            self._data[definition.key] = definition.default

    def get(self, key: str, default: Any = None) -> Any:
        if key in self._data:
            return self._data[key]
        if key in self._definitions:
            return self._definitions[key].default
        return default

    def set(self, key: str, value: Any) -> None:
        old = self._data.get(key)
        if old == value:
            return
        self._data[key] = value
        for listener in self._listeners.get(key, []):
            listener(key, value)
        self._save()

    def set_many(self, values: dict[str, Any]) -> None:
        for key, value in values.items():
            self._data[key] = value
            for listener in self._listeners.get(key, []):
                listener(key, value)
        self._save()

    def reset(self, key: str) -> None:
        if key in self._definitions:
            self.set(key, self._definitions[key].default)

    def reset_all(self) -> None:
        for key, defn in self._definitions.items():
            self._data[key] = defn.default
        self._save()

    def get_category(self, category: str) -> dict[str, Any]:
        keys = [d.key for d in self._definitions.values() if d.category == category]
        return {k: self.get(k) for k in keys}

    def get_definitions(self, category: str = "") -> list[SettingDefinition]:
        if category:
            return [d for d in self._definitions.values() if d.category == category]
        return list(self._definitions.values())

    def categories(self) -> list[str]:
        return list(set(d.category for d in self._definitions.values()))

    def on_change(self, key: str, callback: Callable[[str, Any], None]) -> None:
        self._listeners.setdefault(key, []).append(callback)

    def export_json(self, path: str = "") -> str:
        export_path = path or self.path + ".export"
        with open(export_path, "w") as f:
            json.dump(self._data, f, indent=2)
        return export_path

    def import_json(self, path: str) -> int:
        with open(path) as f:
            data = json.load(f)
        count = 0
        for key, value in data.items():
            if key in self._definitions:
                self._data[key] = value
                count += 1
        self._save()
        return count

    def all(self) -> dict[str, Any]:
        return dict(self._data)

    def _load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path) as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {}

    def _save(self) -> None:
        with open(self.path, "w") as f:
            json.dump(self._data, f, indent=2)

    @staticmethod
    def default_settings(path: str = "lumina_settings.json") -> AppSettings:
        settings = AppSettings(path)
        settings.define(SettingDefinition(
            key="theme", label="Theme", type="choice",
            default="dark", options=["dark", "light"],
            category="appearance",
        ))
        settings.define(SettingDefinition(
            key="language", label="Language", type="choice",
            default="en", options=["en", "zh", "ja", "ko"],
            category="appearance",
        ))
        settings.define(SettingDefinition(
            key="font_size", label="Font Size", type="int",
            default=14, min=8, max=32,
            category="appearance",
        ))
        settings.define(SettingDefinition(
            key="api_key", label="API Key", type="string", default="",
            description="OpenAI API key",
            category="api",
        ))
        settings.define(SettingDefinition(
            key="model", label="Model", type="choice",
            default="gpt-4o", options=["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
            category="api",
        ))
        settings.define(SettingDefinition(
            key="temperature", label="Temperature", type="float",
            default=0.7, min=0.0, max=2.0,
            category="api",
        ))
        settings.define(SettingDefinition(
            key="max_tokens", label="Max Tokens", type="int",
            default=4096, min=256, max=32768,
            category="api",
        ))
        settings.define(SettingDefinition(
            key="auto_save", label="Auto Save", type="bool",
            default=True,
            category="general",
        ))
        settings.define(SettingDefinition(
            key="startup_behavior", label="Startup Behavior", type="choice",
            default="restore", options=["restore", "new", "minimized"],
            category="general",
        ))
        settings.define(SettingDefinition(
            key="log_level", label="Log Level", type="choice",
            default="info", options=["debug", "info", "warning", "error"],
            category="system",
        ))
        return settings
