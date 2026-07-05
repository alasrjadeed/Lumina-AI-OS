class KernelError(Exception):
    """Base kernel exception."""


class ServiceNotFoundError(KernelError):
    def __init__(self, name: str):
        super().__init__(f"Service not found: {name}")


class CircularDependencyError(KernelError):
    def __init__(self, chain: list[str]):
        super().__init__(f"Circular dependency: {' -> '.join(chain)}")


class PluginLoadError(KernelError):
    def __init__(self, name: str, reason: str):
        super().__init__(f"Failed to load plugin '{name}': {reason}")


class EventBusError(KernelError):
    """Event bus error."""


class SchedulerError(KernelError):
    """Scheduler error."""


class RegistrationError(KernelError):
    """Service registration error."""
