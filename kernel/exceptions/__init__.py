class KernelError(Exception):
    pass


class ServiceNotFoundError(KernelError):
    def __init__(self, name: str):
        super().__init__(f"Service not found: {name}")


class PluginLoadError(KernelError):
    def __init__(self, name: str, reason: str):
        super().__init__(f"Failed to load plugin '{name}': {reason}")


class PluginNotDiscoveredError(PluginLoadError):
    def __init__(self, name: str):
        super().__init__(name, "Not discovered")


class PluginVersionError(PluginLoadError):
    def __init__(self, name: str, requirement: str, actual: str):
        super().__init__(name, f"Version {actual} does not satisfy {requirement}")
        self.requirement = requirement
        self.actual = actual


class PluginDependencyError(PluginLoadError):
    def __init__(self, name: str, missing: list[str]):
        super().__init__(name, f"Missing dependencies: {', '.join(missing)}")
        self.missing = missing


class JobNotFoundError(KernelError):
    def __init__(self, job_id: str):
        super().__init__(f"Job not found: {job_id}")


class EventHandlerError(KernelError):
    def __init__(self, event: str, handler: str, reason: str):
        super().__init__(f"Handler '{handler}' failed for event '{event}': {reason}")


class DependencyError(KernelError):
    def __init__(self, service: str, missing: list[str]):
        super().__init__(f"Service '{service}' missing dependencies: {missing}")


class ServiceLifecycleError(KernelError):
    def __init__(self, service: str, message: str):
        super().__init__(f"Service '{service}': {message}")


class CircularDependencyError(KernelError):
    def __init__(self, cycle: list[str]):
        super().__init__(f"Circular dependency detected: {' -> '.join(cycle)}")
