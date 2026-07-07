"""Self-Learning Memory Engine — stores project experiences and improves over time."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field

LEARNING_DIR = os.path.expanduser("~/.lumina/learning")


@dataclass
class ProjectExperience:
    id: str
    project: str
    domain: str
    task: str
    agent: str
    approach: str
    result: str
    duration_ms: float
    success: bool
    learned: str
    tags: list[str] = field(default_factory=list)
    created_at: float = 0.0
    reuse_count: int = 0
    last_reused: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project": self.project,
            "domain": self.domain,
            "task": self.task,
            "agent": self.agent,
            "approach": self.approach,
            "result": self.result,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "learned": self.learned,
            "tags": self.tags,
            "created_at": self.created_at,
            "reuse_count": self.reuse_count,
            "last_reused": self.last_reused,
        }

    @classmethod
    def from_dict(cls, d: dict) -> ProjectExperience:
        return cls(
            id=d["id"], project=d.get("project", ""), domain=d.get("domain", ""),
            task=d["task"], agent=d.get("agent", ""), approach=d.get("approach", ""),
            result=d.get("result", ""), duration_ms=d.get("duration_ms", 0),
            success=d.get("success", True), learned=d.get("learned", ""),
            tags=d.get("tags", []), created_at=d.get("created_at", 0),
            reuse_count=d.get("reuse_count", 0), last_reused=d.get("last_reused", 0),
        )


class LearningEngine:
    """Stores and retrieves project experiences to improve over time."""

    def __init__(self):
        self._experiences: list[ProjectExperience] = []
        self._patterns: dict[str, str] = {}
        self._best_practices: list[str] = []
        self._total_tasks = 0
        self._total_success = 0
        self._load()

    def _path(self) -> str:
        os.makedirs(LEARNING_DIR, exist_ok=True)
        return os.path.join(LEARNING_DIR, "experiences.json")

    def _patterns_path(self) -> str:
        os.makedirs(LEARNING_DIR, exist_ok=True)
        return os.path.join(LEARNING_DIR, "patterns.json")

    def _load(self):
        path = self._path()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                self._experiences = [ProjectExperience.from_dict(d) for d in data[-500:]]
                self._total_tasks = len(self._experiences)
                self._total_success = sum(1 for e in self._experiences if e.success)
            except Exception:
                pass
        ppath = self._patterns_path()
        if os.path.exists(ppath):
            try:
                with open(ppath) as f:
                    data = json.load(f)
                self._patterns = data.get("patterns", {})
                self._best_practices = data.get("best_practices", [])
            except Exception:
                pass

    def _save(self):
        with open(self._path(), "w") as f:
            json.dump([e.to_dict() for e in self._experiences[-500:]], f, indent=2)
        with open(self._patterns_path(), "w") as f:
            json.dump({
                "patterns": self._patterns,
                "best_practices": self._best_practices,
                "stats": self.get_stats(),
            }, f, indent=2)

    async def record(
        self, project: str, domain: str, task: str, agent: str,
        approach: str, result: str, duration_ms: float, success: bool,
        learned: str = "", tags: list[str] | None = None,
    ) -> ProjectExperience:
        import uuid
        exp = ProjectExperience(
            id=uuid.uuid4().hex[:12],
            project=project,
            domain=domain,
            task=task,
            agent=agent,
            approach=approach,
            result=result,
            duration_ms=duration_ms,
            success=success,
            learned=learned,
            tags=tags or [],
            created_at=time.time(),
        )
        self._experiences.append(exp)
        self._total_tasks += 1
        if success:
            self._total_success += 1

        if learned:
            self._extract_pattern(task, learned, domain)

        self._save()
        return exp

    def _extract_pattern(self, task: str, learned: str, domain: str):
        key = domain or "general"
        existing = self._patterns.get(key, "")
        self._patterns[key] = f"{existing}\n- {task}: {learned[:200]}" if existing else f"- {task}: {learned[:200]}"
        self._patterns[key] = "\n".join(self._patterns[key].split("\n")[-20:])

    async def recall_similar(self, task: str, limit: int = 5) -> list[ProjectExperience]:
        task_lower = task.lower()
        scored = []
        for exp in self._experiences:
            score = 0
            for word in task_lower.split():
                if word in exp.task.lower():
                    score += 1
                if word in exp.domain.lower():
                    score += 2
                if word in " ".join(exp.tags).lower():
                    score += 1.5
            if exp.success:
                score *= 1.5
            if score > 0:
                scored.append((score, exp))
        scored.sort(key=lambda x: -x[0])
        return [e for _, e in scored[:limit]]

    async def get_knowledge_for_task(self, task: str) -> str:
        similar = await self.recall_similar(task, limit=3)
        if not similar:
            return ""

        parts = []
        for exp in similar:
            parts.append(
                f"Project: {exp.project}\n"
                f"Task: {exp.task}\n"
                f"Approach: {exp.approach[:500]}\n"
                f"Result: {'SUCCESS' if exp.success else 'FAILED'}\n"
                f"Learned: {exp.learned[:300]}\n"
            )

        return "\n---\n".join(parts)

    async def get_best_practices(self, domain: str = "") -> list[str]:
        if domain:
            return [bp for bp in self._best_practices if domain.lower() in bp.lower()]
        return self._best_practices[:10]

    def mark_reused(self, experience_id: str):
        for exp in self._experiences:
            if exp.id == experience_id:
                exp.reuse_count += 1
                exp.last_reused = time.time()
                self._save()
                return

    async def extract_lesson(self, summary: str) -> str:
        self._best_practices.append(f"[{time.strftime('%Y-%m-%d')}] {summary[:200]}")
        self._best_practices = self._best_practices[-50:]
        self._save()
        return summary

    def get_stats(self) -> dict:
        return {
            "total_experiences": self._total_tasks,
            "total_success": self._total_success,
            "success_rate": round(self._total_success / max(self._total_tasks, 1) * 100, 1),
            "patterns": len(self._patterns),
            "best_practices": len(self._best_practices),
        }

    async def generate_daily_summary(self) -> str:
        recent = [
            e for e in self._experiences
            if time.time() - e.created_at < 86400
        ]
        if not recent:
            return "No tasks completed today."

        successful = [e for e in recent if e.success]
        failed = [e for e in recent if not e.success]
        avg_duration = sum(e.duration_ms for e in recent) / max(len(recent), 1) / 1000

        return (
            f"Today's Summary:\n"
            f"- {len(recent)} tasks processed\n"
            f"- {len(successful)} succeeded, {len(failed)} failed\n"
            f"- Average duration: {avg_duration:.1f}s\n"
            f"- New patterns learned: {len([e for e in recent if e.learned])}\n"
            f"- Success rate: {len(successful)/max(len(recent),1)*100:.1f}%"
        )


learning_engine = LearningEngine()
