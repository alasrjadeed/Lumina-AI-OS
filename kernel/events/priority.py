from enum import IntEnum


class Priority(IntEnum):
    CRITICAL = 0
    HIGH = 25
    NORMAL = 100
    LOW = 200
    BACKGROUND = 500
