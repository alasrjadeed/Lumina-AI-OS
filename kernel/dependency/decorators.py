from __future__ import annotations

import functools
import inspect
import sys
import typing
from collections.abc import Callable
from typing import Any, TypeVar

from kernel.dependency.container import DIContainer
from kernel.dependency.lifetime import Lifetime

F = TypeVar("F", bound=Callable[..., Any])


def inject(
    container: DIContainer | None = None,
) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        sig = inspect.signature(func)
        hints = typing.get_type_hints(func)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if container is None:
                return func(*args, **kwargs)
            bound = sig.bind_partial(*args, **kwargs)
            resolved = dict(bound.arguments)
            for name, param in sig.parameters.items():
                if name in resolved:
                    continue
                if name not in hints:
                    continue
                ann = hints[name]
                if isinstance(ann, type) and container.has(ann):
                    resolved[name] = container.resolve(ann)
                elif param.default is not inspect.Parameter.empty:
                    resolved[name] = param.default
            return func(**resolved)

        wrapper.__di_inject__ = True  # type: ignore[attr-defined]
        return wrapper  # pyright: ignore[reportReturnType]

    return decorator


def service(
    container: DIContainer | None = None,
) -> Callable[[type], type]:
    def decorator(cls: type) -> type:
        cls.__di_registration__ = {"lifetime": Lifetime.TRANSIENT}
        if container is not None:
            container.register_type(cls, lifetime=Lifetime.TRANSIENT)
        return cls

    return decorator


def singleton(
    container: DIContainer | None = None,
) -> Callable[[type], type]:
    def decorator(cls: type) -> type:
        cls.__di_registration__ = {"lifetime": Lifetime.SINGLETON}
        if container is not None:
            container.register_type(cls, lifetime=Lifetime.SINGLETON)
        return cls

    return decorator


def scoped(
    container: DIContainer | None = None,
) -> Callable[[type], type]:
    def decorator(cls: type) -> type:
        cls.__di_registration__ = {"lifetime": Lifetime.SCOPED}
        if container is not None:
            container.register_type(cls, lifetime=Lifetime.SCOPED)
        return cls

    return decorator


def auto_register(
    container: DIContainer,
    *modules: object,
) -> None:
    seen: set[type] = set()
    for mod in modules or list(sys.modules.values()):
        if mod is None:
            continue
        for _name, obj in inspect.getmembers(mod, inspect.isclass):
            if obj in seen:
                continue
            seen.add(obj)
            reg = getattr(obj, "__di_registration__", None)
            if reg is not None:
                container.register_type(obj, lifetime=reg["lifetime"])
