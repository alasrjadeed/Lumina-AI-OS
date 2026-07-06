from __future__ import annotations

import inspect
import typing
from typing import Any

from kernel.dependency.exceptions import (
    CircularDependencyError,
    ServiceNotFoundError,
)


class Resolver:
    def __init__(self) -> None:
        self._resolution_stack: list[str] = []

    def resolve_type(
        self,
        service_type: type,
        container: Any,
    ) -> Any:
        type_name = _type_name(service_type)

        if type_name in self._resolution_stack:
            raise CircularDependencyError(
                [*self._resolution_stack, type_name],
            )

        return self._auto_resolve(service_type, container)

    def resolve_from_container(
        self,
        service_type: type,
        container: Any,
    ) -> Any:
        type_name = _type_name(service_type)

        if type_name in self._resolution_stack:
            raise CircularDependencyError(
                [*self._resolution_stack, type_name],
            )

        registration = container._registry.get(service_type)
        if registration is not None:
            self._resolution_stack.append(type_name)
            try:
                return container._get_from_registration(registration)
            finally:
                self._resolution_stack.pop()

        return self._auto_resolve(service_type, container)

    def _auto_resolve(
        self,
        service_type: type,
        container: Any,
    ) -> Any:
        type_name = _type_name(service_type)
        self._resolution_stack.append(type_name)
        try:
            init = service_type.__init__
            hints = typing.get_type_hints(init)
            sig = inspect.signature(init)
            kwargs: dict[str, Any] = {}

            for name, param in sig.parameters.items():
                if name == "self":
                    continue
                if param.annotation is inspect.Parameter.empty:
                    continue
                dep_type = hints.get(name, param.annotation)
                dep_name = _type_name(dep_type)

                if dep_name in self._resolution_stack:
                    raise CircularDependencyError(
                        [*self._resolution_stack, dep_name],
                    )

                reg = container._registry.get(dep_type)
                if reg is not None:
                    kwargs[name] = container._get_from_registration(reg)
                elif _has_default(param):
                    kwargs[name] = param.default
                else:
                    raise ServiceNotFoundError(dep_name)

            return service_type(**kwargs)
        finally:
            self._resolution_stack.pop()


def _type_name(tp: type) -> str:
    return getattr(tp, "__name__", str(tp))


def _has_default(param: inspect.Parameter) -> bool:
    return param.default is not inspect.Parameter.empty
