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


@dataclass
class Job:
    id: str
    name: str
    task: Any
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retries: int = 0
    max_retries: int = 3
    delay: float = 0.0
    interval: float | None = None
    result: Any = None
    error: str | None = None


@dataclass
class PluginManifest:
    name: str
    version: str
    description: str = ""
    author: str = ""
    dependencies: list[str] = field(default_factory=list)
    entry_point: str = "main"


class ServiceLifetime(Enum):
    SINGLETON = "singleton"
    SCOPED = "scoped"
    TRANSIENT = "transient"


@dataclass
class EventRecord:
    name: str
    data: dict[str, Any] | None = None
    timestamp: float = 0.0
    source: str | None = None
    correlation_id: str | None = None
