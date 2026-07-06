from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from kernel.dependency.lifetime import Lifetime
from kernel.dependency.provider import ServiceProvider


@dataclass
class ServiceRegistration:
    service: str | type
    provider: ServiceProvider
    lifetime: Lifetime = Lifetime.TRANSIENT
    instance: Any = None
    tags: set[str] = field(default_factory=set)
