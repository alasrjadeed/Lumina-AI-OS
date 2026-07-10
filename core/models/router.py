from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ModelCapability:
    name: str
    provider: str
    context_window: int = 4096
    supports_tools: bool = False
    supports_streaming: bool = False
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    capabilities: list[str] = field(default_factory=lambda: ["general"])
    priority: int = 10


TASK_CAPABILITIES: dict[str, list[str]] = {
    "code": ["code", "programming", "debug", "implementation"],
    "reasoning": ["reasoning", "logic", "analysis", "research"],
    "creative": ["creative", "writing", "content", "design"],
    "chat": ["general", "chat", "conversation"],
}


class ModelRouter:
    """Routes requests to the best model based on capability, cost, and availability."""

    def __init__(self, models: list[ModelCapability] | None = None):
        self._models: list[ModelCapability] = models or []

    def add_model(self, model: ModelCapability) -> None:
        self._models.append(model)

    def remove_model(self, name: str) -> None:
        self._models = [m for m in self._models if m.name != name]

    def list_models(self) -> list[ModelCapability]:
        return list(self._models)

    def route(self, task: str, prefer_free: bool = True) -> ModelCapability | None:
        task_lower = task.lower()
        needed = self._detect_capability(task_lower)
        candidates = [m for m in self._models if any(c in m.capabilities for c in needed)]
        if not candidates:
            candidates = list(self._models)
        if prefer_free:
            candidates.sort(
                key=lambda m: (m.cost_per_1k_input + m.cost_per_1k_output, m.priority),
            )
        else:
            candidates.sort(
                key=lambda m: (m.priority, m.cost_per_1k_input + m.cost_per_1k_output),
            )
        return candidates[0] if candidates else None

    def _detect_capability(self, task: str) -> list[str]:
        scores: dict[str, int] = {}
        for cap, keywords in TASK_CAPABILITIES.items():
            scores[cap] = sum(1 for kw in keywords if kw in task)
        if not any(scores.values()):
            return ["chat"]
        max_score = max(scores.values())
        return [cap for cap, score in scores.items() if score == max_score]
