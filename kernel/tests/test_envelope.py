import dataclasses
import enum

from kernel.events.envelope import EventEnvelope, RetryDecision
from kernel.events.event import Event


def test_retry_decision_values():
    assert RetryDecision.RETRY is not None
    assert RetryDecision.FAIL is not None
    assert RetryDecision.DEAD_LETTER is not None
    assert RetryDecision.IGNORE is not None
    assert len(RetryDecision) == 4


def test_retry_decision_is_enum():
    assert issubclass(RetryDecision, enum.Enum)


def test_envelope_creation():
    event = Event(name="test")
    env = EventEnvelope(event=event)
    assert env.event is event
    assert env.attempts == 0
    assert env.last_error is None
    assert env.replay is False


def test_envelope_attempts_increment():
    event = Event(name="test")
    env = EventEnvelope(event=event)
    env.attempts += 1
    assert env.attempts == 1


def test_envelope_replay_flag():
    event = Event(name="test", is_replay=True)
    env = EventEnvelope(event=event, replay=True)
    assert env.replay is True


def test_envelope_last_error():
    event = Event(name="test")
    env = EventEnvelope(event=event, last_error="oops")
    assert env.last_error == "oops"


def test_envelope_is_dataclass():
    assert dataclasses.is_dataclass(EventEnvelope)


def test_envelope_slots():
    env = EventEnvelope(event=Event(name="test"))
    with __import__("pytest").raises(AttributeError):
        env.__dict__
