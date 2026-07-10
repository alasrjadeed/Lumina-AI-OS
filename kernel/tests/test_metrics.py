import pytest

from kernel.events.metrics import EventBusMetrics


def test_default_metrics():
    m = EventBusMetrics()
    assert m.published_events == 0
    assert m.dispatched_events == 0
    assert m.failed_events == 0
    assert m.retried_events == 0
    assert m.active_subscribers == 0
    assert m.queue_depth == 0
    assert m.started_at is not None


def test_uptime_seconds():
    m = EventBusMetrics()
    assert m.uptime_seconds >= 0


def test_snapshot():
    m = EventBusMetrics(
        published_events=10,
        dispatched_events=8,
        failed_events=1,
        retried_events=2,
        active_subscribers=3,
        queue_depth=5,
    )
    s = m.snapshot()
    assert s["published_events"] == 10
    assert s["dispatched_events"] == 8
    assert s["failed_events"] == 1
    assert s["retried_events"] == 2
    assert s["active_subscribers"] == 3
    assert s["queue_depth"] == 5
    assert "started_at" in s
    assert "uptime_seconds" not in s  # property, not in snapshot


def test_slots():
    """EventBusMetrics uses slots to reduce memory."""
    m = EventBusMetrics()
    with pytest.raises(AttributeError):
        m.nonexistent = 1  # pyright: ignore[reportAttributeAccessIssue]
