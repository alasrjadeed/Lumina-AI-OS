from __future__ import annotations

from enum import IntEnum


class Lifetime(IntEnum):
    SINGLETON = 0
    SCOPED = 1
    TRANSIENT = 2
