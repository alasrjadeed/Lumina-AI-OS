from abc import ABC, abstractmethod
from typing import Any, Dict


class ServiceInterface(ABC):
    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]: ...
