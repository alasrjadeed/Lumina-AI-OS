from __future__ import annotations

import json
import os
import time
from enum import Enum
from typing import Any

_CONFIG_DIR = os.path.expanduser("~/.lumina/model_routing")


class TaskType(str, Enum):
    chat = "chat"
    code = "code"
    reasoning = "reasoning"
    creative = "creative"
    analysis = "analysis"
    vision = "vision"
    embedding = "embedding"
    fast = "fast"


class RoutingStrategy(str, Enum):
    manual = "manual"
    cost_optimal = "cost_optimal"
    latency_optimal = "latency_optimal"
    quality_optimal = "quality_optimal"
    fallback_chain = "fallback_chain"


MODEL_PROFILES: dict[str, dict[str, Any]] = {
    "gpt-4o": {"provider": "openai", "cost_per_1k": 0.01, "latency_ms": 800, "quality": 5, "capabilities": ["chat", "code", "reasoning", "analysis", "vision"]},
    "gpt-4o-mini": {"provider": "openai", "cost_per_1k": 0.002, "latency_ms": 400, "quality": 4, "capabilities": ["chat", "code", "fast", "analysis"]},
    "claude-3-opus": {"provider": "anthropic", "cost_per_1k": 0.015, "latency_ms": 1200, "quality": 5, "capabilities": ["chat", "code", "reasoning", "analysis", "creative"]},
    "claude-3-sonnet": {"provider": "anthropic", "cost_per_1k": 0.005, "latency_ms": 600, "quality": 4, "capabilities": ["chat", "code", "reasoning", "analysis"]},
    "llama-3-70b": {"provider": "ollama", "cost_per_1k": 0.0, "latency_ms": 1500, "quality": 3, "capabilities": ["chat", "code", "analysis"]},
    "llama-3-8b": {"provider": "ollama", "cost_per_1k": 0.0, "latency_ms": 500, "quality": 2, "capabilities": ["chat", "fast"]},
    "mixtral-8x7b": {"provider": "ollama", "cost_per_1k": 0.0, "latency_ms": 800, "quality": 3, "capabilities": ["chat", "code", "reasoning"]},
    "gemini-pro": {"provider": "google", "cost_per_1k": 0.001, "latency_ms": 500, "quality": 4, "capabilities": ["chat", "code", "reasoning", "analysis", "vision"]},
    "deepseek-coder": {"provider": "deepseek", "cost_per_1k": 0.001, "latency_ms": 600, "quality": 4, "capabilities": ["code", "reasoning"]},
    "embedding-3": {"provider": "openai", "cost_per_1k": 0.0001, "latency_ms": 200, "quality": 4, "capabilities": ["embedding"]},
}


TASK_ROUTING: dict[str, dict[str, Any]] = {
    "chat": {"strategy": "latency_optimal", "models": ["gpt-4o-mini", "llama-3-8b", "gemini-pro"]},
    "code": {"strategy": "quality_optimal", "models": ["gpt-4o", "claude-3-sonnet", "deepseek-coder"]},
    "reasoning": {"strategy": "quality_optimal", "models": ["deepseek-coder", "claude-3-opus", "gpt-4o", "mixtral-8x7b"]},
    "creative": {"strategy": "quality_optimal", "models": ["claude-3-opus", "gpt-4o"]},
    "analysis": {"strategy": "cost_optimal", "models": ["gpt-4o-mini", "gemini-pro", "claude-3-sonnet"]},
    "vision": {"strategy": "manual", "models": ["gpt-4o", "gemini-pro"]},
    "embedding": {"strategy": "manual", "models": ["embedding-3"]},
    "fast": {"strategy": "latency_optimal", "models": ["llama-3-8b", "gpt-4o-mini"]},
}


class ModelRouter:
    def __init__(self):
        self._routes = dict(TASK_ROUTING)
        self._profiles = dict(MODEL_PROFILES)
        self._usage: dict[str, dict] = {}
        self._load()

    def _path(self, name: str) -> str:
        os.makedirs(_CONFIG_DIR, exist_ok=True)
        return os.path.join(_CONFIG_DIR, name)

    def _load(self) -> None:
        path = self._path("routes.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                    self._routes.update(data.get("routes", {}))
                    self._profiles.update(data.get("profiles", {}))
            except Exception:
                pass
        usage_path = self._path("usage.json")
        if os.path.exists(usage_path):
            try:
                with open(usage_path) as f:
                    self._usage = json.load(f)
            except Exception:
                self._usage = {}

    def _save_routes(self) -> None:
        with open(self._path("routes.json"), "w") as f:
            json.dump({"routes": self._routes, "profiles": self._profiles}, f, indent=2)

    def _save_usage(self) -> None:
        with open(self._path("usage.json"), "w") as f:
            json.dump(self._usage, f, indent=2)

    def get_available_models(self) -> dict[str, dict]:
        return {k: v for k, v in self._profiles.items()}

    def get_routes(self) -> dict:
        return self._routes

    def update_route(self, task_type: str, strategy: str, models: list[str]) -> dict | None:
        if task_type not in self._routes:
            return None
        if strategy not in [s.value for s in RoutingStrategy]:
            return None
        self._routes[task_type] = {"strategy": strategy, "models": models}
        self._save_routes()
        return self._routes[task_type]

    def suggest_model(self, task_type: str, prefer_cost: bool = False) -> dict:
        route = self._routes.get(task_type, self._routes.get("chat"))
        if not route:
            return {"model": "gpt-4o-mini", "provider": "openai", "reason": "fallback"}
        models = route["models"]
        strategy = route["strategy"]

        if prefer_cost:
            strategy = "cost_optimal"

        if strategy == "manual":
            chosen = models[0] if models else "gpt-4o-mini"
        elif strategy == "cost_optimal":
            scored = [(m, self._profiles.get(m, {}).get("cost_per_1k", 999)) for m in models]
            scored.sort(key=lambda x: x[1])
            chosen = scored[0][0]
        elif strategy == "latency_optimal":
            scored = [(m, self._profiles.get(m, {}).get("latency_ms", 999)) for m in models]
            scored.sort(key=lambda x: x[1])
            chosen = scored[0][0]
        elif strategy == "quality_optimal":
            scored = [(m, -self._profiles.get(m, {}).get("quality", 0)) for m in models]
            scored.sort(key=lambda x: x[1])
            chosen = scored[0][0]
        else:
            chosen = models[0] if models else "gpt-4o-mini"

        profile = self._profiles.get(chosen, {})
        self._log_usage(task_type, chosen, profile)
        return {
            "model": chosen,
            "provider": profile.get("provider", "unknown"),
            "strategy": strategy,
            "cost_per_1k": profile.get("cost_per_1k", 0),
            "estimated_latency_ms": profile.get("latency_ms", 0),
            "quality": profile.get("quality", 0),
            "reason": f"Selected via {strategy} from {len(models)} candidates",
        }

    def _log_usage(self, task_type: str, model: str, profile: dict) -> None:
        key = f"{model}:{task_type}"
        entry = self._usage.get(key, {"count": 0, "total_cost": 0.0, "last_used": 0})
        entry["count"] += 1
        entry["total_cost"] += profile.get("cost_per_1k", 0) * 0.001
        entry["last_used"] = time.time()
        self._usage[key] = entry
        self._save_usage()

    def get_usage_stats(self) -> dict:
        total_calls = sum(v["count"] for v in self._usage.values())
        total_cost = sum(v["total_cost"] for v in self._usage.values())
        by_model: dict[str, int] = {}
        for key, v in self._usage.items():
            model = key.split(":")[0]
            by_model[model] = by_model.get(model, 0) + v["count"]
        return {
            "total_calls": total_calls,
            "total_cost": round(total_cost, 4),
            "by_model": by_model,
            "routes": self._routes,
        }

    def reset_usage(self) -> None:
        self._usage = {}
        self._save_usage()


model_router = ModelRouter()
