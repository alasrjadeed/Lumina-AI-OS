import dataclasses
from datetime import UTC, datetime
from uuid import UUID

from kernel.events.event import Event
from kernel.events.subscription import Subscription


async def noop_handler(event: Event):
    return None


def test_subscription_creation():
    sub = Subscription(topic="test.topic", handler=noop_handler)
    assert sub.topic == "test.topic"
    assert sub.handler is noop_handler


def test_subscription_default_priority():
    sub = Subscription(topic="t", handler=noop_handler)
    assert sub.priority == 100


def test_subscription_custom_priority():
    sub = Subscription(topic="t", handler=noop_handler, priority=10)
    assert sub.priority == 10


def test_subscription_enabled_by_default():
    sub = Subscription(topic="t", handler=noop_handler)
    assert sub.enabled is True


def test_subscription_disabled_flag():
    sub = Subscription(topic="t", handler=noop_handler, enabled=False)
    assert sub.enabled is False


def test_subscription_generates_uuid():
    sub = Subscription(topic="t", handler=noop_handler)
    assert isinstance(sub.subscription_id, UUID)


def test_subscription_unique_ids():
    s1 = Subscription(topic="t", handler=noop_handler)
    s2 = Subscription(topic="t", handler=noop_handler)
    assert s1.subscription_id != s2.subscription_id


def test_subscription_created_at():
    before = datetime.now(UTC)
    sub = Subscription(topic="t", handler=noop_handler)
    after = datetime.now(UTC)
    assert before <= sub.created_at <= after


def test_subscription_default_filters():
    sub = Subscription(topic="t", handler=noop_handler)
    assert sub.filters == []


def test_subscription_is_dataclass():
    assert dataclasses.is_dataclass(Subscription)


def test_subscription_slots():
    sub = Subscription(topic="t", handler=noop_handler)
    with __import__("pytest").raises(AttributeError):
        sub.__dict__
