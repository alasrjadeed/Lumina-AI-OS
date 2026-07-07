from __future__ import annotations

import dataclasses
import json
import os
from datetime import datetime


class Episode:
    def __init__(
        self,
        task: str,
        agent: str,
        action: str,
        result: str,
        reflection: str = "",
        duration_ms: float = 0.0,
        success: bool = True,
    ):
        self.task = task
        self.agent = agent
        self.action = action
        self.result = result
        self.reflection = reflection
        self.duration_ms = duration_ms
        self.success = success
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        if dataclasses.is_dataclass(self):
            return dataclasses.asdict(self)
        return vars(self)

    @staticmethod
    def from_dict(d: dict) -> Episode:
        ep = Episode(
            task=d.get("task", ""),
            agent=d.get("agent", ""),
            action=d.get("action", ""),
            result=d.get("result", ""),
            reflection=d.get("reflection", ""),
            duration_ms=d.get("duration_ms", 0.0),
            success=d.get("success", True),
        )
        ep.timestamp = d.get("timestamp", ep.timestamp)
        return ep


class EpisodicMemory:
    """Stores past agent runs for learning and reflection."""

    def __init__(self, path: str = ""):
        self.path = path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "lumina_episodes.json",
        )
        self._episodes: list[Episode] = []
        self._load()

    def record(self, episode: Episode) -> None:
        self._episodes.append(episode)
        self._trim()

    def recent(self, limit: int = 10) -> list[Episode]:
        return self._episodes[-limit:]

    def search(self, query: str, limit: int = 5) -> list[Episode]:
        q = query.lower()
        matches = []
        for ep in reversed(self._episodes):
            if q in ep.task.lower() or q in ep.action.lower() or q in ep.reflection.lower():
                matches.append(ep)
                if len(matches) >= limit:
                    break
        return matches

    def failures(self, limit: int = 10) -> list[Episode]:
        return [ep for ep in reversed(self._episodes) if not ep.success][:limit]

    def lessons(self) -> list[str]:
        return [ep.reflection for ep in self._episodes if ep.reflection.strip()]

    def count(self) -> int:
        return len(self._episodes)

    def clear(self) -> None:
        self._episodes.clear()

    def _trim(self, max_episodes: int = 1000) -> None:
        if len(self._episodes) > max_episodes:
            self._episodes = self._episodes[-max_episodes:]

    def _load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path) as f:
                    data = json.load(f)
                self._episodes = [Episode.from_dict(d) for d in data]
            except (json.JSONDecodeError, OSError):
                self._episodes = []

    def save(self) -> None:
        with open(self.path, "w") as f:
            json.dump([ep.to_dict() for ep in self._episodes], f, indent=2)
