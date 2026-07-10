import pytest

from kernel.events.envelope import EventEnvelope, RetryDecision
from kernel.events.event import Event
from kernel.events.retry import RetryPolicy


def test_default_policy():
    p = RetryPolicy()
    assert p.max_attempts == 3
    assert p.initial_delay == 0.5
    assert p.backoff_multiplier == 2.0
    assert p.max_delay == 30.0
    assert p.retry_exceptions == (Exception,)


def test_custom_policy():
    p = RetryPolicy(
        max_attempts=5,
        initial_delay=1.0,
        backoff_multiplier=3.0,
        max_delay=60.0,
        retry_exceptions=(ValueError, RuntimeError),
    )
    assert p.max_attempts == 5
    assert p.initial_delay == 1.0
    assert p.backoff_multiplier == 3.0
    assert p.max_delay == 60.0
    assert p.retry_exceptions == (ValueError, RuntimeError)


def test_delay_first_attempt():
    """delay_for_attempt(1) returns initial_delay."""
    p = RetryPolicy(initial_delay=1.0, backoff_multiplier=2.0)
    assert p.delay_for_attempt(1) == 1.0


def test_delay_second_attempt():
    p = RetryPolicy(initial_delay=1.0, backoff_multiplier=2.0)
    assert p.delay_for_attempt(2) == 2.0


def test_delay_third_attempt():
    p = RetryPolicy(initial_delay=1.0, backoff_multiplier=2.0)
    assert p.delay_for_attempt(3) == 4.0


def test_delay_fourth_attempt():
    p = RetryPolicy(initial_delay=1.0, backoff_multiplier=2.0)
    assert p.delay_for_attempt(4) == 8.0


def test_delay_fifth_attempt():
    p = RetryPolicy(initial_delay=1.0, backoff_multiplier=2.0)
    assert p.delay_for_attempt(5) == 16.0


def test_delay_capped_by_max():
    p = RetryPolicy(
        initial_delay=1.0,
        backoff_multiplier=10.0,
        max_delay=5.0,
    )
    # Attempt 2: 1.0 * 10^1 = 10.0, capped to 5.0
    assert p.delay_for_attempt(2) == 5.0
    # Attempt 3: 1.0 * 10^2 = 100.0, capped to 5.0
    assert p.delay_for_attempt(3) == 5.0


def test_delay_zero_attempt():
    """max(0, attempt-1) prevents negative exponent."""
    p = RetryPolicy(initial_delay=1.0, backoff_multiplier=2.0)
    assert p.delay_for_attempt(0) == 1.0
    assert p.delay_for_attempt(-1) == 1.0


def test_delay_attempt_sixteen():
    """Very large attempt is capped by max_delay."""
    p = RetryPolicy(max_delay=30.0)
    assert p.delay_for_attempt(16) == 30.0


def test_envelope_defaults():
    e = EventEnvelope(event=Event(name="test"))
    assert e.attempts == 0
    assert e.last_error is None
    assert e.replay is False


def test_envelope_attempts_increment():
    e = EventEnvelope(event=Event(name="test"))
    e.attempts += 1
    assert e.attempts == 1
    e.attempts += 1
    assert e.attempts == 2


def test_envelope_last_error():
    e = EventEnvelope(event=Event(name="test"))
    e.last_error = "something broke"
    assert e.last_error == "something broke"


def test_envelope_replay_flag():
    e = EventEnvelope(event=Event(name="test"), replay=True)
    assert e.replay is True


def test_envelope_immutable_event():
    """Event inside envelope remains frozen."""
    e = EventEnvelope(event=Event(name="test"))
    with pytest.raises(Exception):
        e.event.name = "changed"  # pyright: ignore[reportAttributeAccessIssue]


def test_retry_decision_values():
    assert RetryDecision.RETRY.value == 1
    assert RetryDecision.FAIL.value == 2
    assert RetryDecision.DEAD_LETTER.value == 3
    assert RetryDecision.IGNORE.value == 4


def test_retry_decision_is_enum():
    assert isinstance(RetryDecision.RETRY, RetryDecision)
    assert RetryDecision.RETRY.name == "RETRY"
