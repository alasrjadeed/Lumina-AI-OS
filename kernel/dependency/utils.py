from __future__ import annotations

import inspect
from typing import Any


ServiceKey = str | type


def type_name(tp: type) -> str:
    return getattr(tp, "__name__", str(tp))


def has_default(param: inspect.Parameter) -> bool:
    return param.default is not inspect.Parameter.empty


def ensure_type(key: ServiceKey, label: str = "service") -> type:
    if not isinstance(key, type):
        msg = f"{label} must be a type, got {type(key).__name__}"
        raise TypeError(msg)
    return key


def resolve_annotation(
    hints: dict[str, Any],
    name: str,
    fallback: Any,
) -> type:
    return hints.get(name, fallback)
