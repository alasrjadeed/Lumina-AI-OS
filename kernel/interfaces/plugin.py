from abc import ABC, abstractmethod
from typing import Any, Dict


class PluginInterface(ABC):
    @abstractmethod
    def on_load(self) -> None: ...

    @abstractmethod
    def on_unload(self) -> None: ...

    @abstractmethod
    def on_event(self, event_name: str, data: Dict[str, Any]) -> None: ...
