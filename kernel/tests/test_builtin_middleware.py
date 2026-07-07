from __future__ import annotations

import time
import uuid

import pytest

from kernel.events.builtins.logging import LoggingMiddleware
from kernel.events.builtins.metrics import MetricsMiddleware
from kernel.events.builtins.rate_limit import RateLimitMiddleware, TokenBucket
from kernel.events.builtins.tracing import TracingMiddleware
from kernel.events.builtins.validation import ValidationMiddleware
from kernel.events.event import Event
from kernel.events.subscription import Subscription

# ---------------------------------------------------------------------------
# LoggingMiddleware
# ---------------------------------------------------------------------------

class TestLoggingMiddleware:
    @pytest.fixture
    def mw(self):
        return LoggingMiddleware(level="debug")

    @pytest.mark.asyncio
    async def test_before_publish_returns_event(self, mw):
        e = Event(name="test")
        result = await mw.before_publish(e)
        assert result is e

    @pytest.mark.asyncio
    async def test_after_publish_does_not_raise(self, mw):
        await mw.after_publish(Event(name="test"))

    @pytest.mark.asyncio
    async def test_before_dispatch_returns_event(self, mw):
        e = Event(name="test")
        result = await mw.before_dispatch(e)
        assert result is e

    @pytest.mark.asyncio
    async def test_before_handler_returns_event(self, mw):
        sub = Subscription(topic="t", handler=lambda e: None)
        e = Event(name="test")
        result = await mw.before_handler(sub, e)
        assert result is e

    @pytest.mark.asyncio
    async def test_after_handler_does_not_raise(self, mw):
        sub = Subscription(topic="t", handler=lambda e: None)
        await mw.after_handler(sub, Event(name="test"))

    @pytest.mark.asyncio
    async def test_on_exception_does_not_raise(self, mw):
        sub = Subscription(topic="t", handler=lambda e: None)
        await mw.on_exception(sub, Event(name="test"), ValueError("x"))

    @pytest.mark.asyncio
    async def test_after_dispatch_does_not_raise(self, mw):
        await mw.after_dispatch(Event(name="test"))


# ---------------------------------------------------------------------------
# MetricsMiddleware
# ---------------------------------------------------------------------------

class TestMetricsMiddleware:
    @pytest.fixture
    def mw(self):
        return MetricsMiddleware()

    @pytest.mark.asyncio
    async def test_before_publish_records_timestamp(self, mw):
        e = Event(name="a", correlation_id="c1")
        await mw.before_publish(e)
        assert "c1" in mw._timestamps

    @pytest.mark.asyncio
    async def test_after_publish_increments_published(self, mw):
        await mw.after_publish(Event(name="a"))
        assert mw._per_type["a"].published == 1

    @pytest.mark.asyncio
    async def test_after_handler_tracks_duration(self, mw):
        e = Event(name="a", correlation_id="c1")
        await mw.before_publish(e)
        await mw.after_handler(Subscription(topic="t", handler=lambda e: None), e)
        assert mw._per_type["a"].dispatched == 1
        assert mw._per_type["a"].total_duration > 0

    @pytest.mark.asyncio
    async def test_on_exception_increments_failed(self, mw):
        e = Event(name="a")
        await mw.on_exception(Subscription(topic="t", handler=lambda e: None), e, ValueError("x"))
        assert mw._per_type["a"].failed == 1

    @pytest.mark.asyncio
    async def test_snapshot(self, mw):
        await mw.after_publish(Event(name="x"))
        snap = mw.snapshot()
        assert "x" in snap
        assert snap["x"]["published"] == 1

    @pytest.mark.asyncio
    async def test_per_type_property(self, mw):
        await mw.after_publish(Event(name="y"))
        assert "y" in mw.per_type


# ---------------------------------------------------------------------------
# ValidationMiddleware
# ---------------------------------------------------------------------------

class TestValidationMiddleware:
    @pytest.fixture
    def mw(self):
        return ValidationMiddleware()

    @pytest.mark.asyncio
    async def test_passes_without_validators(self, mw):
        e = Event(name="test")
        result = await mw.before_publish(e)
        assert result is e

    @pytest.mark.asyncio
    async def test_validator_passes(self, mw):
        e = Event(name="test", payload=42)
        mw.add_validator("test", lambda ev: ev.payload == 42)
        result = await mw.before_publish(e)
        assert result is e

    @pytest.mark.asyncio
    async def test_validator_rejects(self, mw):
        e = Event(name="test", payload=0)
        mw.add_validator("test", lambda ev: ev.payload == 42)
        with pytest.raises(Exception, match="Validation failed"):
            await mw.before_publish(e)

    @pytest.mark.asyncio
    async def test_validator_scoped_to_event_name(self, mw):
        e = Event(name="other", payload=99)
        mw.add_validator("test", lambda ev: False)
        result = await mw.before_publish(e)
        assert result is e

    @pytest.mark.asyncio
    async def test_remove_validator(self, mw):
        def v(ev):
            return True
        mw.add_validator("t", v)
        assert mw.remove_validator("t", v) is True
        assert "t" not in mw._validators

    @pytest.mark.asyncio
    async def test_remove_nonexistent_validator(self, mw):
        assert mw.remove_validator("x", lambda ev: True) is False

    @pytest.mark.asyncio
    async def test_multiple_validators_all_pass(self, mw):
        e = Event(name="test", payload="ok")
        mw.add_validator("test", lambda ev: bool(ev.payload))
        mw.add_validator("test", lambda ev: isinstance(ev.payload, str))
        result = await mw.before_publish(e)
        assert result is e

    @pytest.mark.asyncio
    async def test_multiple_validators_one_fails(self, mw):
        e = Event(name="test", payload="ok")
        mw.add_validator("test", lambda ev: bool(ev.payload))
        mw.add_validator("test", lambda ev: False)
        with pytest.raises(Exception, match="Validation failed"):
            await mw.before_publish(e)


# ---------------------------------------------------------------------------
# TracingMiddleware
# ---------------------------------------------------------------------------

class TestTracingMiddleware:
    @pytest.fixture
    def mw(self):
        return TracingMiddleware()

    @pytest.mark.asyncio
    async def test_before_publish_adds_correlation_id(self, mw):
        e = Event(name="test")
        result = await mw.before_publish(e)
        assert result is not e
        assert result.correlation_id != ""

    @pytest.mark.asyncio
    async def test_before_publish_preserves_existing_id(self, mw):
        e = Event(name="test", correlation_id="existing-123")
        result = await mw.before_publish(e)
        assert result is e
        assert result.correlation_id == "existing-123"

    @pytest.mark.asyncio
    async def test_before_handler_propagates_id(self, mw):
        e = Event(name="test", correlation_id="abc")
        sub = Subscription(topic="t", handler=lambda e: None)
        result = await mw.before_handler(sub, e)
        assert result.correlation_id == "abc"

    @pytest.mark.asyncio
    async def test_before_handler_no_id_does_nothing(self, mw):
        e = Event(name="test")
        sub = Subscription(topic="t", handler=lambda e: None)
        result = await mw.before_handler(sub, e)
        assert result.correlation_id == ""

    @pytest.mark.asyncio
    async def test_generated_id_is_uuid(self, mw):
        e = Event(name="test")
        result = await mw.before_publish(e)
        assert uuid.UUID(result.correlation_id)

    @pytest.mark.asyncio
    async def test_propagate_false_returns_same_event(self, mw):
        mw._propagate = False
        e = Event(name="test", correlation_id="abc")
        sub = Subscription(topic="t", handler=lambda e: None)
        result = await mw.before_handler(sub, e)
        assert result is e


# ---------------------------------------------------------------------------
# TokenBucket
# ---------------------------------------------------------------------------

class TestTokenBucket:
    def test_initial_tokens(self):
        tb = TokenBucket(rate=10, burst=5)
        for _ in range(5):
            assert tb.consume() is True
        assert tb.consume() is False

    def test_refills_over_time(self):
        tb = TokenBucket(rate=10, burst=5)
        for _ in range(5):
            tb.consume()
        time.sleep(0.2)
        assert tb.consume() is True


# ---------------------------------------------------------------------------
# RateLimitMiddleware
# ---------------------------------------------------------------------------

class TestRateLimitMiddleware:
    @pytest.fixture
    def mw(self):
        return RateLimitMiddleware(default_rate=1000, default_burst=10)

    @pytest.mark.asyncio
    async def test_allows_within_limit(self, mw):
        e = Event(name="test")
        result = await mw.before_publish(e)
        assert result is e

    @pytest.mark.asyncio
    async def test_blocks_over_limit(self):
        mw = RateLimitMiddleware(default_rate=0.001, default_burst=1)
        e = Event(name="test")
        await mw.before_publish(e)
        with pytest.raises(RuntimeError, match="Rate limit exceeded"):
            await mw.before_publish(e)

    @pytest.mark.asyncio
    async def test_per_source_buckets(self):
        mw = RateLimitMiddleware(default_rate=0.001, default_burst=1)
        e1 = Event(name="a", source="src1")
        e2 = Event(name="b", source="src2")
        await mw.before_publish(e1)
        result = await mw.before_publish(e2)
        assert result is e2

    @pytest.mark.asyncio
    async def test_set_rate_override(self, mw):
        mw.set_rate("critical", rate=1.0, burst=100)
        assert "critical" in mw._overrides
