from __future__ import annotations

import inspect

ServiceKey = str | type


def type_name(tp: type) -> str:
    return getattr(tp, "__name__", str(tp))


def has_default(param: inspect.Parameter) -> bool:
    return param.default is not inspect.Parameter.empty
