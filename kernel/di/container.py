import inspect
from typing import Any

from kernel.log import setup_log
from kernel.models import ServiceLifetime

log = setup_log("di")


class DIContainer:
    def __init__(self):
        self._bindings: dict[str, dict] = {}

    def bind(
        self,
        abstract: str,
        concrete: type | Any,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    ):
        self._bindings[abstract] = {
            "concrete": concrete,
            "lifetime": lifetime,
            "instance": None,
        }
        cname = concrete.__name__ if isinstance(concrete, type) else concrete
        log.debug("Bound: %s -> %s (%s)", abstract, cname, lifetime.value)

    def resolve(self, abstract: str) -> Any:
        binding = self._bindings.get(abstract)
        if not binding:
            raise ValueError(f"No binding for: {abstract}")

        if binding["lifetime"] == ServiceLifetime.SINGLETON:
            if binding["instance"] is None:
                binding["instance"] = self._build(binding["concrete"])
            return binding["instance"]

        if binding["lifetime"] == ServiceLifetime.SCOPED:
            return self._build(binding["concrete"])

        return self._build(binding["concrete"])

    def _build(self, concrete: type) -> Any:
        if not isinstance(concrete, type):
            return concrete
        sig = inspect.signature(concrete.__init__)
        params = {}
        for name, param in sig.parameters.items():
            if name == "self":
                continue
            ann = param.annotation
            if hasattr(ann, "__name__") and ann.__name__ in self._bindings:
                params[name] = self.resolve(param.annotation.__name__)
            elif param.default is not inspect.Parameter.empty:
                params[name] = param.default
        return concrete(**params)

    def has(self, abstract: str) -> bool:
        return abstract in self._bindings

    def clear(self):
        self._bindings.clear()
