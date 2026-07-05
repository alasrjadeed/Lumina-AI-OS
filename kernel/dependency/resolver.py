import inspect
import logging
from typing import Any, Callable, Dict, get_type_hints

from kernel.dependency.container import DIContainer

logger = logging.getLogger(__name__)


class Resolver:
    def __init__(self, container: DIContainer):
        self._container = container

    def resolve_callable(self, func: Callable) -> Dict[str, Any]:
        sig = inspect.signature(func)
        hints = get_type_hints(func)
        resolved: Dict[str, Any] = {}

        for param_name, param in sig.parameters.items():
            if param_name == "self" or param_name == "cls":
                continue
            if param.default is not inspect.Parameter.empty:
                continue
            if param_name in hints:
                hint = hints[param_name]
                if hasattr(hint, "__name__"):
                    try:
                        resolved[param_name] = self._container.resolve(
                            hint.__name__.lower()
                        )
                    except KeyError:
                        pass
        return resolved

    def call_with_dependencies(self, func: Callable, **kwargs) -> Any:
        resolved = self.resolve_callable(func)
        resolved.update(kwargs)
        return func(**resolved)
