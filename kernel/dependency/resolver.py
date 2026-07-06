from __future__ import annotations

import inspect
import typing
from typing import Any

from kernel.dependency.exceptions import (
    CircularDependencyError,
    ServiceNotFoundError,
)
from kernel.dependency.utils import has_default, type_name


class Resolver:
    def __init__(self) -> None:
        self._resolution_stack: list[str] = []

    def resolve_type(
        self,
        service_type: type,
        container: Any,
    ) -> Any:
        tn = type_name(service_type)

        if tn in self._resolution_stack:
            raise CircularDependencyError(
                [*self._resolution_stack, tn],
            )

        return self._auto_resolve(service_type, container)

    def resolve_from_container(
        self,
        service_type: type,
        container: Any,
    ) -> Any:
        tn = type_name(service_type)

        if tn in self._resolution_stack:
            raise CircularDependencyError(
                [*self._resolution_stack, tn],
            )

        registration = container._registry.get(service_type)
        if registration is not None:
            self._resolution_stack.append(tn)
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
        tn = type_name(service_type)
        self._resolution_stack.append(tn)
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
                dep_name = type_name(dep_type)

                if dep_name in self._resolution_stack:
                    raise CircularDependencyError(
                        [*self._resolution_stack, dep_name],
                    )

                reg = container._registry.get(dep_type)
                if reg is not None:
                    kwargs[name] = container._get_from_registration(reg)
                elif has_default(param):
                    kwargs[name] = param.default
                else:
                    raise ServiceNotFoundError(dep_name)

            return service_type(**kwargs)
        finally:
            self._resolution_stack.pop()
