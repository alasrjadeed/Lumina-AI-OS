from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from kernel.scheduler.models import Job as Job
from kernel.scheduler.models import JobStatus as JobStatus


class ServiceLifetime(Enum):
    SINGLETON = "singleton"
    SCOPED = "scoped"
    TRANSIENT = "transient"


class PluginStatus(Enum):
    DISCOVERED = "discovered"
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class PluginType(Enum):
    STANDARD = "standard"
    SYSTEM = "system"
    EXTENSION = "extension"
    THEME = "theme"


@dataclass
class PluginManifest:
    name: str
    version: str
    description: str = ""
    author: str = ""
    homepage: str = ""
    license: str = ""
    dependencies: list[str] = field(default_factory=list)
    entry_point: str = "main"
    tags: list[str] = field(default_factory=list)
    plugin_type: PluginType = PluginType.STANDARD
    version_requirements: dict[str, str] = field(default_factory=dict)
    python_version: str = ">=3.10"
    kernel_version: str = ">=0.1.0"


@dataclass
class EventRecord:
    name: str
    data: dict[str, Any] | None = None
    timestamp: float = 0.0
    source: str | None = None
    correlation_id: str | None = None
