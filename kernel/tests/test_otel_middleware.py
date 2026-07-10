import pytest

from kernel.events.builtins import otel as otel_mod
from kernel.events.builtins.otel import OpenTelemetryMiddleware
from kernel.events.event import Event
from kernel.events.subscription import Subscription

pytest.importorskip("opentelemetry")


class TestOpenTelemetryMiddleware:
    @pytest.fixture
    def mw(self):
        return OpenTelemetryMiddleware()

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
    async def test_after_dispatch_does_not_raise(self, mw):
        await mw.after_dispatch(Event(name="test"))

    @pytest.mark.asyncio
    async def test_before_handler_returns_event(self, mw):
        sub = Subscription(topic="t", handler=lambda e: None)  # pyright: ignore[reportArgumentType]
        e = Event(name="test")
        result = await mw.before_handler(sub, e)
        assert result is e

    @pytest.mark.asyncio
    async def test_after_handler_does_not_raise(self, mw):
        sub = Subscription(topic="t", handler=lambda e: None)  # pyright: ignore[reportArgumentType]
        await mw.after_handler(sub, Event(name="test"))

    @pytest.mark.asyncio
    async def test_on_exception_does_not_raise(self, mw):
        sub = Subscription(topic="t", handler=lambda e: None)  # pyright: ignore[reportArgumentType]
        await mw.on_exception(sub, Event(name="test"), ValueError("x"))

    @pytest.mark.asyncio
    async def test_custom_span_prefix(self):
        mw = OpenTelemetryMiddleware(span_prefix="custom")
        e = Event(name="test")
        result = await mw.before_publish(e)
        assert result is e


def test_otel_available_flag():
    assert otel_mod._OTEL_AVAILABLE is True


def test_otel_missing_import_raises(monkeypatch):
    monkeypatch.setattr("kernel.events.builtins.otel._OTEL_AVAILABLE", False)
    with pytest.raises(RuntimeError, match="opentelemetry-api"):
        OpenTelemetryMiddleware()
