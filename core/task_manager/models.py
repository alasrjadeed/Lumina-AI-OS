from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class TaskPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class TaskStep:
    id: str = ""
    name: str = ""
    agent: str = ""
    description: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    progress_label: str = ""
    result: Any = None
    error: str = ""
    started: float = 0.0
    completed: float = 0.0


@dataclass
class TaskEvent:
    type: str = ""
    task_id: str = ""
    step_id: str = ""
    status: str = ""
    progress: int = 0
    progress_label: str = ""
    message: str = ""
    timestamp: float = 0.0


@dataclass
class Task:
    id: str = ""
    name: str = ""
    description: str = ""
    priority: TaskPriority = TaskPriority.NORMAL
    tags: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    progress_label: str = ""
    steps: list[TaskStep] = field(default_factory=list)
    result: Any = None
    error: str = ""
    created: float = field(default_factory=time.time)
    started: float = 0.0
    completed: float = 0.0
    duration_ms: float = 0.0
    max_retries: int = 2
    retry_count: int = 0
    schedule_at: float = 0.0
    parent_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def total_steps(self) -> int:
        return len(self.steps)

    def completed_steps(self) -> int:
        return sum(
            1
            for s in self.steps
            if s.status in (TaskStatus.COMPLETED, TaskStatus.SKIPPED, TaskStatus.FAILED)
        )

    def failed_steps(self) -> int:
        return sum(1 for s in self.steps if s.status == TaskStatus.FAILED)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority.name,
            "tags": self.tags,
            "status": self.status.value,
            "progress": self.progress,
            "progress_label": self.progress_label,
            "steps": [
                {
                    "id": s.id,
                    "name": s.name,
                    "agent": s.agent,
                    "description": s.description,
                    "status": s.status.value,
                    "progress": s.progress,
                    "progress_label": s.progress_label,
                    "error": s.error[:200] if s.error else "",
                }
                for s in self.steps
            ],
            "error": self.error[:300] if self.error else "",
            "created": self.created,
            "started": self.started,
            "completed": self.completed,
            "duration_ms": self.duration_ms,
            "parent_id": self.parent_id,
            "metadata": self.metadata,
        }

    def emit_event(
        self, type: str = "task.update", step_id: str = "", message: str = ""
    ) -> TaskEvent:
        return TaskEvent(
            type=type,
            task_id=self.id,
            step_id=step_id,
            status=self.status.value,
            progress=self.progress,
            progress_label=self.progress_label,
            message=message,
            timestamp=time.time(),
        )
