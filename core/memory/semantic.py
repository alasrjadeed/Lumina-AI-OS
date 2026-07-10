from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any


class Fact:
    def __init__(
        self,
        subject: str,
        predicate: str,
        obj: str,
        confidence: float = 1.0,
        source: str = "",
    ):
        self.subject = subject
        self.predicate = predicate
        self.obj = obj
        self.confidence = confidence
        self.source = source
        self.timestamp = datetime.now().isoformat()
        self.count = 1

    def to_dict(self) -> dict:
        return vars(self)

    @staticmethod
    def from_dict(d: dict) -> Fact:
        f = Fact(
            subject=d.get("subject", ""),
            predicate=d.get("predicate", ""),
            obj=d.get("obj", ""),
            confidence=d.get("confidence", 1.0),
            source=d.get("source", ""),
        )
        f.timestamp = d.get("timestamp", f.timestamp)
        f.count = d.get("count", 1)
        return f

    def key(self) -> str:
        return f"{self.subject}|{self.predicate}|{self.obj}"


class SemanticMemory:
    """Stores extracted facts and learned patterns."""

    def __init__(self, path: str = ""):
        self.path = path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "lumina_semantic.json",
        )
        self._facts: dict[str, Fact] = {}
        self._patterns: list[dict[str, Any]] = []
        self._load()

    def learn(self, fact: Fact) -> None:
        key = fact.key()
        if key in self._facts:
            existing = self._facts[key]
            existing.count += 1
            existing.confidence = min(1.0, existing.confidence + 0.1)
            existing.timestamp = datetime.now().isoformat()
        else:
            self._facts[key] = fact

    def query(
        self,
        subject: str = "",
        predicate: str = "",
        obj: str = "",
        min_confidence: float = 0.0,
    ) -> list[Fact]:
        results = []
        for f in self._facts.values():
            if f.confidence < min_confidence:
                continue
            if subject and subject.lower() not in f.subject.lower():
                continue
            if predicate and predicate.lower() not in f.predicate.lower():
                continue
            if obj and obj.lower() not in f.obj.lower():
                continue
            results.append(f)
        return results

    def know(self, subject: str, predicate: str, obj: str) -> bool:
        return self.query(subject=subject, predicate=predicate, obj=obj, min_confidence=0.5) != []

    def add_pattern(self, pattern: dict[str, Any]) -> None:
        self._patterns.append({**pattern, "timestamp": datetime.now().isoformat()})

    def patterns(self, tag: str = "") -> list[dict[str, Any]]:
        if tag:
            return [p for p in self._patterns if p.get("tag") == tag]
        return list(self._patterns)

    def count_facts(self) -> int:
        return len(self._facts)

    def clear(self) -> None:
        self._facts.clear()
        self._patterns.clear()

    def _load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path) as f:
                    data = json.load(f)
                self._facts = {k: Fact.from_dict(v) for k, v in data.get("facts", {}).items()}
                self._patterns = data.get("patterns", [])
            except (json.JSONDecodeError, OSError):
                pass

    def save(self) -> None:
        with open(self.path, "w") as f:
            json.dump(
                {
                    "facts": {k: v.to_dict() for k, v in self._facts.items()},
                    "patterns": self._patterns,
                },
                f,
                indent=2,
            )
