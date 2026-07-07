from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from core.vision.camera import Frame
from core.vision.detector import DetectionResult
from core.vision.description import SceneDescription
from core.vision.face import FaceResult


@dataclass
class Observation:
    timestamp: float
    frame: Frame | None = None
    detections: DetectionResult | None = None
    faces: FaceResult | None = None
    description: SceneDescription | None = None
    summary: str = ""
    labels: list[str] = field(default_factory=list)
    people_count: int = 0

    @property
    def age_seconds(self) -> float:
        return time.time() - self.timestamp

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "age_seconds": round(self.age_seconds, 1),
            "summary": self.summary,
            "labels": self.labels,
            "people_count": self.people_count,
            "has_frame": self.frame is not None,
            "detection_count": self.detections.count if self.detections else 0,
            "face_count": self.faces.count if self.faces else 0,
            "description": self.description.summary if self.description else "",
        }


class VisualShortTermMemory:
    def __init__(self, capacity: int = 30, ttl_seconds: float = 120.0):
        self._observations: deque[Observation] = deque(maxlen=capacity)
        self._ttl = ttl_seconds
        self._capacity = capacity
        self._current: Observation | None = None

    @property
    def current(self) -> Observation | None:
        return self._current

    @property
    def size(self) -> int:
        return len(self._observations)

    @property
    def capacity(self) -> int:
        return self._capacity

    def push(self, obs: Observation) -> None:
        self._current = obs
        self._observations.append(obs)
        self._evict_expired()

    def get_recent(self, seconds: float = 60.0) -> list[Observation]:
        now = time.time()
        return [o for o in self._observations if now - o.timestamp <= seconds]

    def get_all(self) -> list[Observation]:
        return list(self._observations)

    def clear(self) -> None:
        self._observations.clear()
        self._current = None

    def get_by_label(self, label: str) -> list[Observation]:
        return [o for o in self._observations if label in o.labels]

    def has_seen(self, label: str, within_seconds: float = 30.0) -> bool:
        now = time.time()
        return any(
            label in o.labels and (now - o.timestamp) <= within_seconds
            for o in self._observations
        )

    def _evict_expired(self) -> None:
        now = time.time()
        while self._observations and (now - self._observations[0].timestamp) > self._ttl:
            self._observations.popleft()

    def summary(self, max_observations: int = 3) -> str:
        if not self._observations:
            return "I haven't seen anything yet."
        recent = list(self._observations)[-max_observations:]
        parts = []
        for o in recent:
            age = o.age_seconds
            age_str = f"{age:.0f}s ago" if age < 60 else f"{age/60:.0f}m ago"
            if o.summary:
                parts.append(f"[{age_str}] {o.summary}")
            elif o.labels:
                parts.append(f"[{age_str}] Saw: {', '.join(o.labels)}")
        return "\n".join(parts) if parts else "Nothing notable observed."

    def change_detected(self, new_obs: Observation) -> str | None:
        if not self._observations:
            return None
        prev = self._observations[-1]
        new_labels = set(new_obs.labels)
        prev_labels = set(prev.labels)

        appeared = new_labels - prev_labels
        disappeared = prev_labels - new_labels

        changes = []
        if appeared:
            changes.append(f"I see {', '.join(appeared)} now")
        if disappeared:
            changes.append(f"{', '.join(disappeared)} are gone")

        if new_obs.people_count > prev.people_count:
            changes.append("someone joined")
        elif new_obs.people_count < prev.people_count:
            changes.append("someone left")

        return ". ".join(changes) + "." if changes else None
