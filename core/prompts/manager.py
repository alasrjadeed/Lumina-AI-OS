from __future__ import annotations

from datetime import datetime
from typing import Any

DEFAULT_TEMPLATES: dict[str, dict[str, str]] = {
    "chat": {
        "system": (
            "You are a helpful AI assistant. "
            "Answer the user's questions accurately and concisely."
        ),
        "user": "{message}",
    },
    "code": {
        "system": (
            "You are an expert programmer. Generate {language} code. "
            "Return only the code block.\nRequirements: {description}"
        ),
        "user": "Write {language} code for: {description}",
    },
    "agent": {
        "system": (
            "You are {agent_name}. {agent_description}\n"
            "Complete the following task thoroughly."
        ),
        "user": "{task}",
    },
    "summary": {
        "system": "Summarize the following content concisively, capturing key points.",
        "user": "{content}",
    },
    "analysis": {
        "system": (
            "Analyze the following content in detail. "
            "Provide insights, patterns, and recommendations."
        ),
        "user": "{content}",
    },
    "reflect": {
        "system": (
            "You are reflecting on a completed task. "
            "Evaluate what went well, what could be improved, and what was learned."
        ),
        "user": "Task: {task}\nResult: {result}",
    },
}


class PromptManager:
    """Manages prompt templates with versioning and variable substitution."""

    def __init__(self, templates: dict[str, dict[str, str]] | None = None):
        self._templates: dict[str, dict[str, str]] = {}
        self._versions: dict[str, int] = {}
        self._history: dict[str, list[dict[str, Any]]] = {}
        self.load(templates or DEFAULT_TEMPLATES)

    def load(self, templates: dict[str, dict[str, str]]) -> None:
        for name, tmpl in templates.items():
            self._templates[name] = tmpl
            self._versions[name] = self._versions.get(name, 0) + 1
            version = self._versions[name]
            self._history.setdefault(name, []).append({
                "version": version,
                "template": tmpl,
                "timestamp": datetime.now().isoformat(),
            })

    def get(self, name: str, version: int | None = None) -> dict[str, str] | None:
        if version is None:
            return self._templates.get(name)
        hist = self._history.get(name, [])
        for h in hist:
            if h["version"] == version:
                return h["template"]
        return None

    def render(
        self, name: str,
        variables: dict[str, str] | None = None,
        version: int | None = None,
    ) -> list[dict[str, str]]:
        tmpl = self.get(name, version)
        if not tmpl:
            raise ValueError(f"Unknown template: {name}")
        result = []
        for role, text in tmpl.items():
            content = text
            if variables:
                for key, value in variables.items():
                    content = content.replace(f"{{{key}}}", str(value))
            result.append({"role": role, "content": content})
        return result

    def register(self, name: str, template: dict[str, str]) -> None:
        self._templates[name] = template
        self._versions[name] = self._versions.get(name, 0) + 1
        self._history.setdefault(name, []).append({
            "version": self._versions[name],
            "template": template,
            "timestamp": datetime.now().isoformat(),
        })

    def list_templates(self) -> list[str]:
        return sorted(self._templates.keys())

    def get_version(self, name: str) -> int:
        return self._versions.get(name, 0)

    def get_history(self, name: str) -> list[dict[str, Any]]:
        return list(self._history.get(name, []))
