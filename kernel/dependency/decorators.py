from __future__ import annotations

import functools
from typing import Any, Callable, TypeVar

from kernel.dependency.container import DIContainer
from kernel.dependency.lifetime import Lifetime

F = TypeVar("F", bound=Callable[..., Any])


def inject(func: F) -> F:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    wrapper.__di_inject__ = True  # type: ignore[attr-defined]
    return wrapper


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
    import inspect
    import sys

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
