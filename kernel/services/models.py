from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any

HealthChecker = Callable[[], "HealthStatus | None"]


class ServiceStatus(Enum):
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class HealthStatus(Enum):
    HEALTHY = auto()
    DEGRADED = auto()
    UNHEALTHY = auto()


@dataclass
class ServiceRecord:
    name: str
    instance: Any
    status: ServiceStatus = ServiceStatus.CREATED
    tags: set[str] = field(default_factory=set)
    dependencies: list[str] = field(default_factory=list)
    health_checkers: list[HealthChecker] = field(default_factory=list)
    health: HealthStatus | None = None
    last_health_check: datetime | None = None
    error: str | None = None
    started_at: datetime | None = None
    stopped_at: datetime | None = None
