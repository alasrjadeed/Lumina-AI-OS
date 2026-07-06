from kernel.exceptions import KernelError


class InvalidEventError(KernelError):
    def __init__(self, reason: str) -> None:
        super().__init__(f"Invalid event: {reason}")


class DuplicateSubscriberError(KernelError):
    def __init__(self, topic: str) -> None:
        super().__init__(f"Handler already registered for '{topic}'")


class EventValidationError(KernelError):
    def __init__(self, reason: str) -> None:
        super().__init__(f"Event validation failed: {reason}")


class EventSubscriberError(KernelError):
    def __init__(self, reason: str) -> None:
        super().__init__(f"Subscriber execution failed: {reason}")
