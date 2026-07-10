import pytest

from kernel.events.event import Event
from kernel.events.filters import (
    CompositeFilter,
    NameFilter,
    PayloadValueFilter,
    PredicateFilter,
    SourceFilter,
)
from kernel.events.subscription import Subscription


def make_event(
    name: str = "test",
    source: str = "",
    payload=None,
) -> Event:
    return Event(name=name, source=source, payload=payload)


class TestSourceFilter:
    def test_matches_correct_source(self):
        f = SourceFilter("voice")
        assert f.matches(make_event(source="voice"))

    def test_rejects_different_source(self):
        f = SourceFilter("voice")
        assert not f.matches(make_event(source="microphone"))

    def test_rejects_empty_source(self):
        f = SourceFilter("voice")
        assert not f.matches(make_event(source=""))


class TestNameFilter:
    def test_matches_exact_name(self):
        f = NameFilter("kernel.started")
        assert f.matches(make_event(name="kernel.started"))

    def test_rejects_different_name(self):
        f = NameFilter("kernel.started")
        assert not f.matches(make_event(name="kernel.stopped"))


class TestPayloadValueFilter:
    def test_matches_key_value(self):
        f = PayloadValueFilter("language", "en")
        assert f.matches(make_event(payload={"language": "en"}))

    def test_rejects_wrong_value(self):
        f = PayloadValueFilter("language", "en")
        assert not f.matches(make_event(payload={"language": "fr"}))

    def test_rejects_missing_key(self):
        f = PayloadValueFilter("language", "en")
        assert not f.matches(make_event(payload={}))

    def test_rejects_none_payload(self):
        f = PayloadValueFilter("language", "en")
        assert not f.matches(make_event(payload=None))


class TestPredicateFilter:
    def test_matches_true_predicate(self):
        f = PredicateFilter(lambda e: e.name == "test")
        assert f.matches(make_event(name="test"))

    def test_rejects_false_predicate(self):
        f = PredicateFilter(lambda e: False)
        assert not f.matches(make_event())


class TestCompositeFilter:
    def test_all_pass_delivers(self):
        f = CompositeFilter(
            SourceFilter("voice"),
            PayloadValueFilter("language", "en"),
        )
        assert f.matches(
            make_event(source="voice", payload={"language": "en"}),
        )

    def test_one_fails_rejects(self):
        f = CompositeFilter(
            SourceFilter("voice"),
            PayloadValueFilter("language", "en"),
        )
        assert not f.matches(
            make_event(source="microphone", payload={"language": "en"}),
        )

    def test_all_fail_rejects(self):
        f = CompositeFilter(
            SourceFilter("voice"),
            PayloadValueFilter("language", "en"),
        )
        assert not f.matches(
            make_event(source="microphone", payload={"language": "fr"}),
        )

    def test_empty_composite_passes(self):
        f = CompositeFilter()
        assert f.matches(make_event())


@pytest.mark.asyncio
class TestFilterWithBus:
    async def test_empty_filter_list_allows_all(self, started_bus):
        bus = started_bus
        received = []

        async def handler(event: Event):
            received.append(event.name)

        await bus.register(
            Subscription(topic="*", handler=handler, filters=[]),
        )
        await bus.publish(Event(name="a"))
        await bus.publish(Event(name="b"))
        await bus.join()

        assert received == ["a", "b"]

    async def test_source_filter_on_bus(self, started_bus):
        bus = started_bus
        received = []

        async def handler(event: Event):
            received.append((event.name, event.source))

        await bus.register(
            Subscription(
                topic="*",
                handler=handler,
                filters=[SourceFilter("voice")],
            ),
        )
        await bus.publish(Event(name="e1", source="voice"))
        await bus.publish(Event(name="e2", source="microphone"))
        await bus.publish(Event(name="e3", source="voice"))
        await bus.join()

        assert received == [("e1", "voice"), ("e3", "voice")]

    async def test_multiple_filters_independent_subs(self, started_bus):
        bus = started_bus
        voice_received = []
        mic_received = []

        async def voice_handler(event: Event):
            voice_received.append(event.name)

        async def mic_handler(event: Event):
            mic_received.append(event.name)

        await bus.register(
            Subscription(
                topic="*",
                handler=voice_handler,
                filters=[SourceFilter("voice")],
            ),
        )
        await bus.register(
            Subscription(
                topic="*",
                handler=mic_handler,
                filters=[SourceFilter("microphone")],
            ),
        )
        await bus.publish(Event(name="e1", source="voice"))
        await bus.publish(Event(name="e2", source="microphone"))
        await bus.join()

        assert voice_received == ["e1"]
        assert mic_received == ["e2"]

    async def test_filter_and_topic_both_apply(self, started_bus):
        bus = started_bus
        received = []

        async def handler(event: Event):
            received.append(event.name)

        await bus.register(
            Subscription(
                topic="voice.*",
                handler=handler,
                filters=[SourceFilter("microphone")],
            ),
        )
        await bus.publish(Event(name="voice.command", source="microphone"))
        await bus.publish(Event(name="voice.command", source="speaker"))
        await bus.publish(Event(name="ui.click", source="microphone"))
        await bus.join()

        assert received == ["voice.command"]

    async def test_multiple_filters_with_payload(self, started_bus):
        bus = started_bus
        received = []

        async def handler(event: Event):
            received.append(event.payload)

        await bus.register(
            Subscription(
                topic="*",
                handler=handler,
                filters=[
                    SourceFilter("sensor"),
                    PayloadValueFilter("type", "temperature"),
                ],
            ),
        )
        await bus.publish(
            Event(
                name="sensor.reading",
                source="sensor",
                payload={"type": "temperature", "value": 22},
            ),
        )
        await bus.publish(
            Event(
                name="sensor.reading",
                source="sensor",
                payload={"type": "humidity", "value": 60},
            ),
        )
        await bus.publish(
            Event(
                name="sensor.reading",
                source="camera",
                payload={"type": "temperature", "value": 30},
            ),
        )
        await bus.join()

        assert received == [{"type": "temperature", "value": 22}]

    async def test_predicate_filter_on_bus(self, started_bus):
        bus = started_bus
        received = []

        async def handler(event: Event):
            received.append(event.payload)

        await bus.register(
            Subscription(
                topic="*",
                handler=handler,
                filters=[
                    PredicateFilter(lambda e: (e.payload or {}).get("confidence", 0) > 0.9),
                ],
            ),
        )
        await bus.publish(
            Event(name="pred", payload={"confidence": 0.95}),
        )
        await bus.publish(
            Event(name="pred", payload={"confidence": 0.5}),
        )
        await bus.join()

        assert received == [{"confidence": 0.95}]

    async def test_filters_respect_priority_order(self, started_bus):
        bus = started_bus
        order = []

        async def low_handler(event: Event):
            order.append("low")

        async def high_handler(event: Event):
            order.append("high")

        await bus.register(
            Subscription(
                topic="*",
                handler=low_handler,
                priority=200,
                filters=[SourceFilter("voice")],
            ),
        )
        await bus.register(
            Subscription(
                topic="*",
                handler=high_handler,
                priority=100,
                filters=[SourceFilter("voice")],
            ),
        )
        await bus.publish(Event(name="t", source="voice"))
        await bus.join()

        assert order == ["high", "low"]

    async def test_filtered_subscriber_not_counted_as_dispatched(
        self,
        started_bus,
    ):
        bus = started_bus

        async def handler(event: Event):
            pass

        await bus.register(
            Subscription(
                topic="*",
                handler=handler,
                filters=[SourceFilter("nowhere")],
            ),
        )
        await bus.publish(Event(name="t", source="voice"))
        await bus.join()

        assert bus.metrics().dispatched_events == 0

    async def test_composite_filter_on_bus(self, started_bus):
        bus = started_bus
        received = []

        async def handler(event: Event):
            received.append(event.name)

        await bus.register(
            Subscription(
                topic="*",
                handler=handler,
                filters=[
                    CompositeFilter(
                        SourceFilter("sensor"),
                        PayloadValueFilter("critical", True),
                    ),
                ],
            ),
        )
        await bus.publish(
            Event(
                name="alert",
                source="sensor",
                payload={"critical": True},
            ),
        )
        await bus.publish(
            Event(
                name="alert",
                source="sensor",
                payload={"critical": False},
            ),
        )
        await bus.publish(
            Event(
                name="alert",
                source="ui",
                payload={"critical": True},
            ),
        )
        await bus.join()

        assert received == ["alert"]
