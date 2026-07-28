"""Preference Store — learns user preferences from corrections."""

from __future__ import annotations

import json
import os
import re


_DEFAULT_PATH = os.path.expanduser("~/.lumina/preferences.json")


class PreferenceStore:
    def __init__(self, path: str = _DEFAULT_PATH):
        self.path = path
        self._data: dict[str, dict[str, str]] = {}
        self._load()

    def _load(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if os.path.exists(self.path):
            try:
                with open(self.path) as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {}

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self._data, f, indent=2)

    def get_category(self, category: str) -> dict[str, str]:
        return self._data.get(category, {})

    def set_category(self, category: str, prefs: dict[str, str]) -> None:
        self._data[category] = prefs
        self._save()

    def set(self, category: str, key: str, value: str) -> None:
        if category not in self._data:
            self._data[category] = {}
        self._data[category][key] = value
        self._save()

    def get(self, category: str, key: str, default: str | None = None) -> str | None:
        return self._data.get(category, {}).get(key, default)

    def delete(self, category: str, key: str) -> bool:
        if category in self._data and key in self._data[category]:
            del self._data[category][key]
            self._save()
            return True
        return False

    def all(self) -> dict[str, dict[str, str]]:
        return self._data

    def clear(self) -> None:
        self._data = {}
        self._save()


_CORRECTION_PATTERNS = [
    (r"no[,\s]+(?:open|run|start|use|launch)\s+(\S+)", "app_aliases"),
    (r"i\s+meant\s+(?:open|run|start|use|launch)\s+(\S+)", "app_aliases"),
    (r"not\s+(?:that|this|it)[,\s]+(?:but|open|run|start|use|launch)\s+(\S+)", "app_aliases"),
    (r"wrong[,\s]+(?:open|run|start|use|launch)\s+(\S+)", "app_aliases"),
    (r"use\s+(\S+)\s+instead", "app_aliases"),
    (r"don'?t\s+use\s+(\S+)[,\s]+use\s+(\S+)", "app_aliases"),
    (r"(\w+)\s+not\s+(\w+)", "command_patterns"),
]


def detect_correction(user_input: str, last_action: str | None = None) -> dict | None:
    """Detect user corrections and return learned preference if found."""
    user_lower = user_input.lower()

    for pattern, category in _CORRECTION_PATTERNS:
        match = re.search(pattern, user_lower)
        if match:
            groups = match.groups()
            store = PreferenceStore()

            if len(groups) >= 2 and pattern.startswith(r"don'?t"):
                key = groups[0]
                value = groups[1]
                store.set(category, key, value)
                return {"key": key, "value": value, "category": category}

            if len(groups) >= 1:
                key = groups[0]
                value = groups[1] if len(groups) > 1 else last_action or key
                store.set(category, key, value)
                return {"key": key, "value": value, "category": category}

    return None


def apply_preferences(user_input: str) -> str:
    """Apply learned preferences to modify user input."""
    store = PreferenceStore()
    modified = user_input

    app_aliases = store.get_category("app_aliases")
    for alias, actual in app_aliases.items():
        pattern = re.compile(rf'\b{re.escape(alias)}\b', re.IGNORECASE)
        if pattern.search(modified):
            modified = pattern.sub(actual, modified)

    return modified
