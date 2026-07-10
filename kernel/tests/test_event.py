import time

import pytest

from kernel.events.event import Event


def test_event_creation():
    e = Event(name="test.event", payload=42, source="test")
    assert e.name == "test.event"
    assert e.payload == 42
    assert e.source == "test"
    assert e.is_replay is False
    assert e.correlation_id == ""
    assert e.version == 0


def test_event_default_timestamp():
    now = time.time()
    e = Event(name="test")
    assert abs(e.timestamp - now) < 1.0


def test_event_is_frozen():
    e = Event(name="test")
    with __import__("pytest").raises(AttributeError):
        e.name = "changed"  # pyright: ignore[reportAttributeAccessIssue]


def test_event_requires_non_empty_name():
    with pytest.raises(ValueError, match="non-empty string"):
        Event(name="")


def test_event_rejects_non_string_name():
    with pytest.raises(ValueError):
        Event(name=123)  # pyright: ignore[reportArgumentType]


def test_event_default_source():
    e = Event(name="test.event")
    assert e.source == ""


def test_event_replay_flag():
    e = Event(name="replayed", is_replay=True)
    assert e.is_replay is True


def test_event_correlation_id():
    e = Event(name="corr", correlation_id="abc-123")
    assert e.correlation_id == "abc-123"


def test_event_version_default():
    e = Event(name="v")
    assert e.version == 0
