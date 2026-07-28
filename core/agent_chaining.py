from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any

_CHAIN_DIR = os.path.expanduser("~/.lumina/chains")


class ChainStep:
    def __init__(self, agent: str, prompt: str, step_id: str | None = None, depends_on: list[str] | None = None):
        self.id = step_id or uuid.uuid4().hex[:8]
        self.agent = agent
        self.prompt = prompt
        self.depends_on = depends_on or []
        self.output: str = ""

    def to_dict(self) -> dict:
        return {"id": self.id, "agent": self.agent, "prompt": self.prompt, "depends_on": self.depends_on, "output": self.output[:200] if self.output else ""}

    @classmethod
    def from_dict(cls, d: dict) -> ChainStep:
        s = cls(agent=d["agent"], prompt=d["prompt"], step_id=d.get("id"), depends_on=d.get("depends_on", []))
        s.output = d.get("output", "")
        return s


class Chain:
    def __init__(self, name: str, description: str = "", chain_id: str | None = None):
        self.id = chain_id or uuid.uuid4().hex[:12]
        self.name = name
        self.description = description
        self.steps: list[ChainStep] = []
        self.created_at = time.time()
        self.updated_at = time.time()

    def add_step(self, agent: str, prompt: str, depends_on: list[str] | None = None) -> str:
        step = ChainStep(agent=agent, prompt=prompt, depends_on=depends_on)
        self.steps.append(step)
        self.updated_at = time.time()
        return step.id

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "step_count": len(self.steps),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Chain:
        c = cls(name=d["name"], description=d.get("description", ""), chain_id=d.get("id"))
        c.steps = [ChainStep.from_dict(s) for s in d.get("steps", [])]
        c.created_at = d.get("created_at", time.time())
        c.updated_at = d.get("updated_at", time.time())
        return c


class ChainStore:
    def __init__(self):
        self._chains: list[Chain] = []
        self._load()

    def _path(self, name: str) -> str:
        os.makedirs(_CHAIN_DIR, exist_ok=True)
        return os.path.join(_CHAIN_DIR, name)

    def _load(self) -> None:
        path = self._path("chains.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    self._chains = [Chain.from_dict(d) for d in json.load(f)]
            except Exception:
                self._chains = []

    def _save(self) -> None:
        with open(self._path("chains.json"), "w") as f:
            json.dump([c.to_dict() for c in self._chains], f, indent=2)

    def create(self, name: str, description: str = "") -> Chain:
        chain = Chain(name=name, description=description)
        self._chains.append(chain)
        self._save()
        return chain

    def list(self) -> list[Chain]:
        return sorted(self._chains, key=lambda c: c.updated_at, reverse=True)

    def get(self, chain_id: str) -> Chain | None:
        for c in self._chains:
            if c.id == chain_id:
                return c
        return None

    def update(self, chain_id: str, **kwargs) -> Chain | None:
        c = self.get(chain_id)
        if not c:
            return None
        for k, v in kwargs.items():
            if hasattr(c, k):
                setattr(c, k, v)
        c.updated_at = time.time()
        self._save()
        return c

    def delete(self, chain_id: str) -> bool:
        for i, c in enumerate(self._chains):
            if c.id == chain_id:
                self._chains.pop(i)
                self._save()
                return True
        return False

    def add_step(self, chain_id: str, agent: str, prompt: str, depends_on: list[str] | None = None) -> str | None:
        c = self.get(chain_id)
        if not c:
            return None
        step_id = c.add_step(agent, prompt, depends_on)
        self._save()
        return step_id

    def update_step_output(self, chain_id: str, step_id: str, output: str) -> bool:
        c = self.get(chain_id)
        if not c:
            return False
        for step in c.steps:
            if step.id == step_id:
                step.output = output
                self._save()
                return True
        return False


chain_store = ChainStore()
