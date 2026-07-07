from __future__ import annotations

from dataclasses import dataclass, field

from kernel.dependency.lifetime import Lifetime
from kernel.dependency.provider import ServiceProvider


@dataclass
class ServiceRegistration:
    service: str | type
    provider: ServiceProvider
    lifetime: Lifetime = Lifetime.TRANSIENT
    tags: set[str] = field(default_factory=set)
