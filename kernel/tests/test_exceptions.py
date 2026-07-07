from kernel.events.exceptions import (
    DuplicateSubscriberError,
    EventSubscriberError,
    EventValidationError,
    InvalidEventError,
)
from kernel.exceptions import KernelError


def test_invalid_event_error():
    err = InvalidEventError("bad name")
    assert str(err) == "Invalid event: bad name"
    assert isinstance(err, KernelError)


def test_duplicate_subscriber_error():
    err = DuplicateSubscriberError("test.topic")
    assert str(err) == "Handler already registered for 'test.topic'"
    assert isinstance(err, KernelError)


def test_event_validation_error():
    err = EventValidationError("payload too large")
    assert str(err) == "Event validation failed: payload too large"
    assert isinstance(err, KernelError)


def test_event_subscriber_error():
    err = EventSubscriberError("timeout")
    assert str(err) == "Subscriber execution failed: timeout"
    assert isinstance(err, KernelError)


def test_all_exceptions_are_kernel_errors():
    for exc_cls in [
        InvalidEventError,
        DuplicateSubscriberError,
        EventValidationError,
        EventSubscriberError,
    ]:
        instance = exc_cls("test")
        assert isinstance(instance, KernelError), f"{exc_cls.__name__} is not a KernelError"


def test_exception_with_no_argument():
    try:
        raise EventSubscriberError("boom")
    except KernelError as e:
        assert str(e) == "Subscriber execution failed: boom"
