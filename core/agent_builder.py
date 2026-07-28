from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any

_BUILDER_DIR = os.path.expanduser("~/.lumina/agent_blueprints")

BUILTIN_TOOLS = ["calculator", "web_search", "json_parse", "base64_encode", "base64_decode", "word_count", "char_count", "uuid_gen", "timestamp", "echo"]


class AgentBlueprint:
    def __init__(
        self,
        name: str,
        description: str = "",
        system_prompt: str = "",
        tools: list[str] | None = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        blueprint_id: str | None = None,
    ):
        self.id = blueprint_id or uuid.uuid4().hex[:12]
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.created_at = time.time()
        self.updated_at = time.time()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "tools": self.tools,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> AgentBlueprint:
        b = cls(
            name=d["name"],
            description=d.get("description", ""),
            system_prompt=d.get("system_prompt", ""),
            tools=d.get("tools", []),
            model=d.get("model", "gpt-4o-mini"),
            temperature=d.get("temperature", 0.7),
            max_tokens=d.get("max_tokens", 2048),
            blueprint_id=d.get("id"),
        )
        b.created_at = d.get("created_at", time.time())
        b.updated_at = d.get("updated_at", time.time())
        return b


class BlueprintStore:
    def __init__(self):
        self._blueprints: list[AgentBlueprint] = []
        self._load()

    def _path(self, name: str) -> str:
        os.makedirs(_BUILDER_DIR, exist_ok=True)
        return os.path.join(_BUILDER_DIR, name)

    def _load(self) -> None:
        path = self._path("blueprints.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    self._blueprints = [AgentBlueprint.from_dict(d) for d in json.load(f)]
            except Exception:
                self._blueprints = []

    def _save(self) -> None:
        with open(self._path("blueprints.json"), "w") as f:
            json.dump([b.to_dict() for b in self._blueprints], f, indent=2)

    def create(self, name: str, description: str = "", system_prompt: str = "", tools: list[str] | None = None, model: str = "gpt-4o-mini", temperature: float = 0.7, max_tokens: int = 2048) -> AgentBlueprint:
        bp = AgentBlueprint(name=name, description=description, system_prompt=system_prompt, tools=tools or [], model=model, temperature=temperature, max_tokens=max_tokens)
        self._blueprints.append(bp)
        self._save()
        return bp

    def list(self) -> list[AgentBlueprint]:
        return sorted(self._blueprints, key=lambda b: b.updated_at, reverse=True)

    def get(self, blueprint_id: str) -> AgentBlueprint | None:
        for b in self._blueprints:
            if b.id == blueprint_id:
                return b
        return None

    def update(self, blueprint_id: str, **kwargs) -> AgentBlueprint | None:
        bp = self.get(blueprint_id)
        if not bp:
            return None
        for k, v in kwargs.items():
            if hasattr(bp, k):
                setattr(bp, k, v)
        bp.updated_at = time.time()
        self._save()
        return bp

    def delete(self, blueprint_id: str) -> bool:
        for i, b in enumerate(self._blueprints):
            if b.id == blueprint_id:
                self._blueprints.pop(i)
                self._save()
                return True
        return False

    def duplicate(self, blueprint_id: str) -> AgentBlueprint | None:
        bp = self.get(blueprint_id)
        if not bp:
            return None
        return self.create(
            name=f"{bp.name} (copy)",
            description=bp.description,
            system_prompt=bp.system_prompt,
            tools=list(bp.tools),
            model=bp.model,
            temperature=bp.temperature,
            max_tokens=bp.max_tokens,
        )

    def get_stats(self) -> dict:
        return {
            "total_blueprints": len(self._blueprints),
            "unique_models": len(set(b.model for b in self._blueprints)),
        }


blueprint_store = BlueprintStore()
