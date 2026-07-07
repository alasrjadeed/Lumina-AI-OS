import os
import tempfile

import pytest

from kernel.events.dead_letter import DeadLetterEntry
from kernel.events.event import Event
from kernel.events.event_bus import EventBus
from kernel.events.sqlite_dlq import SqliteDeadLetterQueue
from kernel.events.subscription import Subscription


@pytest.fixture
def db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def dlq(db_path):
    return SqliteDeadLetterQueue(db_path)


class TestSqliteDeadLetterQueue:
    def test_add_and_count(self, dlq):
        entry = DeadLetterEntry(
            event=Event(name="test.event", payload={"key": "val"}, source="src"),
            exception="Something broke",
            exception_type="ValueError",
            subscriber="my_handler",
        )
        dlq.add(entry)
        assert dlq.count() == 1

    def test_add_multiple(self, dlq):
        for i in range(5):
            dlq.add(DeadLetterEntry(
                event=Event(name=f"e{i}"),
                exception=f"err{i}",
            ))
        assert dlq.count() == 5

    def test_all_returns_entries(self, dlq):
        dlq.add(DeadLetterEntry(
            event=Event(name="a"),
            exception="err",
            subscriber="h1",
        ))
        dlq.add(DeadLetterEntry(
            event=Event(name="b"),
            exception="err2",
            subscriber="h2",
        ))
        entries = dlq.all()
        assert len(entries) == 2
        assert entries[0].event.name == "a"
        assert entries[1].event.name == "b"

    def test_latest_returns_most_recent(self, dlq):
        for i in range(5):
            dlq.add(DeadLetterEntry(
                event=Event(name=f"e{i}"),
                exception=f"err{i}",
            ))
        latest = dlq.latest(limit=2)
        assert len(latest) == 2
        assert latest[0].event.name == "e4"
        assert latest[1].event.name == "e3"

    def test_clear(self, dlq):
        dlq.add(DeadLetterEntry(event=Event(name="x"), exception="err"))
        dlq.clear()
        assert dlq.count() == 0

    def test_max_entries_respected(self, db_path):
        dlq = SqliteDeadLetterQueue(db_path, max_entries=3)
        for i in range(5):
            dlq.add(DeadLetterEntry(
                event=Event(name=f"e{i}"),
                exception=f"err{i}",
            ))
        assert dlq.count() == 3

    def test_event_fields_preserved(self, dlq):
        ev = Event(
            name="order.created",
            payload={"order_id": 123},
            source="orders",
            correlation_id="corr-abc",
            version=2,
            is_replay=True,
            timestamp=1000.0,
        )
        dlq.add(DeadLetterEntry(
            event=ev,
            exception="timeout",
            exception_type="TimeoutError",
            subscriber="order_handler",
            attempts=3,
        ))
        entries = dlq.all()
        e = entries[0]
        assert e.event.name == "order.created"
        assert e.event.payload == {"order_id": 123}
        assert e.event.source == "orders"
        assert e.event.correlation_id == "corr-abc"
        assert e.event.version == 2
        assert e.event.is_replay is True
        assert e.event.timestamp == 1000.0
        assert e.exception == "timeout"
        assert e.exception_type == "TimeoutError"
        assert e.subscriber == "order_handler"
        assert e.attempts == 3

    def test_entry_without_event(self, dlq):
        dlq.add(DeadLetterEntry(exception="no event"))
        entries = dlq.all()
        assert len(entries) == 1
        assert entries[0].event is None
        assert entries[0].exception == "no event"

    @pytest.mark.asyncio
    async def test_swappable_dlq_backend(self, db_path):

        bus = EventBus()
        sqlite_dlq = SqliteDeadLetterQueue(db_path)
        bus.set_dlq_backend(sqlite_dlq)

        bus.start()

        async def failing_handler(event):
            raise ValueError("handler fail")

        sub = Subscription(topic="test.dlq", handler=failing_handler)
        await bus.register(sub)
        await bus.publish(Event(name="test.dlq", payload={}, source="test"))
        await bus.join()
        await bus.shutdown()

        assert bus.dead_letter_count() > 0
        entries = bus.dead_letters()
        assert any("handler fail" in e.exception for e in entries)
