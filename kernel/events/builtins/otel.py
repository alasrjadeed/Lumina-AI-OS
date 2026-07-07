from __future__ import annotations

from typing import TYPE_CHECKING, Any

from kernel.events.event import Event
from kernel.events.middleware import BaseMiddleware

if TYPE_CHECKING:
    from kernel.events.subscription import Subscription

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode

    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False


class OpenTelemetryMiddleware(BaseMiddleware):
    def __init__(
        self,
        tracer: Any | None = None,
        span_prefix: str = "eventbus",
    ) -> None:
        if not _OTEL_AVAILABLE:
            raise RuntimeError(
                "OpenTelemetryMiddleware requires opentelemetry-api. "
                "Install with: pip install opentelemetry-api"
            )
        self._tracer = tracer or trace.get_tracer(__name__)
        self._span_prefix = span_prefix
        self._spans: dict[str, Any] = {}

    async def before_publish(self, event: Event) -> Event:
        span = self._tracer.start_span(
            f"{self._span_prefix}.publish",
            attributes={
                "event.name": event.name,
                "event.source": event.source or "",
                "event.version": event.version,
            },
        )
        span.add_event("publish.start", {"event.name": event.name})
        self._spans[event.correlation_id or event.name] = span
        return event

    async def after_publish(self, event: Event) -> None:
        key = event.correlation_id or event.name
        span = self._spans.pop(key, None)
        if span is not None:
            span.add_event("publish.end", {"event.name": event.name})

    async def before_dispatch(self, event: Event) -> Event:
        span = self._tracer.start_span(
            f"{self._span_prefix}.dispatch",
            attributes={
                "event.name": event.name,
                "event.source": event.source or "",
            },
        )
        key = f"dispatch:{event.correlation_id or event.name}"
        self._spans[key] = span
        return event

    async def after_dispatch(self, event: Event) -> None:
        key = f"dispatch:{event.correlation_id or event.name}"
        span = self._spans.pop(key, None)
        if span is not None:
            span.set_attribute("dispatch.complete", True)
            span.end()

    async def before_handler(
        self,
        subscription: Subscription,
        event: Event,
    ) -> Event:
        span = self._tracer.start_span(
            f"{self._span_prefix}.handler",
            attributes={
                "event.name": event.name,
                "subscription.topic": subscription.topic,
                "subscription.priority": subscription.priority,
            },
        )
        key = f"handler:{event.correlation_id or event.name}:{subscription.subscription_id}"
        self._spans[key] = span
        return event

    async def after_handler(
        self,
        subscription: Subscription,
        event: Event,
    ) -> None:
        key = f"handler:{event.correlation_id or event.name}:{subscription.subscription_id}"
        span = self._spans.pop(key, None)
        if span is not None:
            span.set_attribute("handler.complete", True)
            span.end()

    async def on_exception(
        self,
        subscription: Subscription,
        event: Event,
        exception: Exception,
    ) -> None:
        key = f"handler:{event.correlation_id or event.name}:{subscription.subscription_id}"
        span = self._spans.pop(key, None)
        if span is not None:
            span.set_status(Status(StatusCode.ERROR, str(exception)))
            span.record_exception(exception)
            span.end()
