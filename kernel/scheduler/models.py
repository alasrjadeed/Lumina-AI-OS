from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


TaskFunc = Callable[..., Any]


@dataclass
class Job:
    id: str
    name: str
    task: TaskFunc
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retries: int = 0
    max_retries: int = 3
    delay: float = 0.0
    interval: float | None = None
    cron: str | None = None
    result: Any = None
    error: str | None = None
    tags: set[str] = field(default_factory=set)
    auto_remove: bool = False
    max_executions: int | None = None
    execution_count: int = 0
    start_at: datetime | None = None
    end_at: datetime | None = None
