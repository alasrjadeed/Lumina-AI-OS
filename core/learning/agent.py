"""Learning Agent — records actions, recognizes patterns, accelerates repetitive tasks."""

from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from core.log import log


@dataclass
class ActionRecord:
    """A recorded user action with context."""

    action: str
    params: dict[str, Any] = field(default_factory=dict)
    module: str = ""
    timestamp: float = field(default_factory=time.time)
    success: bool = True
    duration_ms: float = 0.0


@dataclass
class Pattern:
    """A learned pattern from repeated actions."""

    sequence: list[str]
    frequency: int = 1
    last_used: float = field(default_factory=time.time)
    context: str = ""
    suggestions: list[dict] = field(default_factory=list)


class LearningAgent:
    """Records actions, learns patterns, and predicts next steps.

    The more you use Lumina, the faster it becomes at anticipating
    your needs and automating repetitive workflows.
    """

    def __init__(self, storage_path: str = "learning_data.json"):
        self.storage_path = storage_path
        self._history: list[ActionRecord] = []
        self._patterns: list[Pattern] = []
        self._field_memory: dict[str, dict[str, str]] = defaultdict(dict)
        self._workflows: dict[str, list[dict]] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
            self._history = [ActionRecord(**h) for h in data.get("history", [])]
            self._patterns = [Pattern(**p) for p in data.get("patterns", [])]
            self._field_memory = defaultdict(dict, data.get("field_memory", {}))
            self._workflows = data.get("workflows", {})
        except Exception:
            pass

    def _save(self) -> None:
        with open(self.storage_path, "w") as f:
            json.dump(
                {
                    "history": [
                        {
                            "action": h.action,
                            "params": h.params,
                            "module": h.module,
                            "timestamp": h.timestamp,
                            "success": h.success,
                            "duration_ms": h.duration_ms,
                        }
                        for h in self._history[-500:]
                    ],
                    "patterns": [
                        {
                            "sequence": p.sequence,
                            "frequency": p.frequency,
                            "last_used": p.last_used,
                            "context": p.context,
                            "suggestions": p.suggestions,
                        }
                        for p in self._patterns
                    ],
                    "field_memory": dict(self._field_memory),
                    "workflows": self._workflows,
                },
                f,
                indent=2,
            )

    # ── Record Actions ──

    def record(
        self,
        action: str,
        module: str = "",
        params: dict | None = None,
        success: bool = True,
        duration_ms: float = 0.0,
    ) -> None:
        record = ActionRecord(
            action=action,
            module=module,
            params=params or {},
            success=success,
            duration_ms=duration_ms,
        )
        self._history.append(record)
        self._learn_pattern(record)
        if len(self._history) > 1000:
            self._history = self._history[-500:]
        self._save()

    def _learn_pattern(self, record: ActionRecord) -> None:
        recent = [r for r in self._history[-10:] if r.success]
        if len(recent) >= 3:
            seq = [f"{r.module}:{r.action}" if r.module else r.action for r in recent[-3:]]
            existing = next((p for p in self._patterns if p.sequence == seq), None)
            if existing:
                existing.frequency += 1
                existing.last_used = time.time()
            else:
                self._patterns.append(Pattern(sequence=seq, frequency=1))

    # ── Field Memory ──

    def remember_field(self, form_id: str, field_name: str, value: str) -> None:
        """Remember a field value for auto-fill on similar forms."""
        self._field_memory[form_id][field_name] = value
        self._save()

    def get_field(self, form_id: str, field_name: str) -> str | None:
        """Get remembered field value."""
        return self._field_memory.get(form_id, {}).get(field_name)

    def suggest_fields(self, form_id: str) -> dict[str, str]:
        """Get all remembered fields for a form."""
        return dict(self._field_memory.get(form_id, {}))

    # ── Pattern Recognition ──

    def suggest_next_action(self, recent_actions: list[str]) -> str | None:
        """Predict the next action based on past patterns."""
        for pattern in sorted(self._patterns, key=lambda p: p.frequency, reverse=True):
            if pattern.sequence[:-1] == recent_actions:
                return pattern.sequence[-1]
        return None

    def get_frequent_patterns(self, limit: int = 5) -> list[Pattern]:
        return sorted(self._patterns, key=lambda p: p.frequency, reverse=True)[:limit]

    # ── Workflows ──

    def save_workflow(self, name: str, steps: list[dict]) -> None:
        """Save a named workflow (sequence of actions)."""
        self._workflows[name] = steps
        self._save()
        log.info("Learning: Workflow saved: %s (%d steps)", name, len(steps))

    def get_workflow(self, name: str) -> list[dict] | None:
        return self._workflows.get(name)

    def list_workflows(self) -> list[str]:
        return list(self._workflows.keys())

    def run_workflow(self, name: str) -> dict:
        """Execute a saved workflow."""
        steps = self._workflows.get(name)
        if not steps:
            return {"error": f"Workflow '{name}' not found"}
        results = [{"step": step, "status": "ready"} for step in steps]
        return {"workflow": name, "steps": len(steps), "results": results}

    # ── Statistics ──

    def get_stats(self) -> dict:
        return {
            "total_actions": len(self._history),
            "patterns_learned": len(self._patterns),
            "fields_remembered": sum(len(v) for v in self._field_memory.values()),
            "workflows_saved": len(self._workflows),
            "top_patterns": [
                {"sequence": p.sequence, "frequency": p.frequency}
                for p in self.get_frequent_patterns(3)
            ],
        }


agent = LearningAgent()
