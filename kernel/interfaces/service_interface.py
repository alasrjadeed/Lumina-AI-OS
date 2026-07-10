from typing import Protocol, runtime_checkable


@runtime_checkable
class IService(Protocol):
    @property
    def service_name(self) -> str: ...

    async def initialize(self) -> None: ...

    async def shutdown(self) -> None: ...
