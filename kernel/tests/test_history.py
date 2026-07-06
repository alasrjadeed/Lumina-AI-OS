import pytest

from kernel.events.event import Event
from kernel.events.history import EventHistory


def test_store_and_count():
    h = EventHistory(max_events=10)
    assert h.count() == 0
    assert len(h) == 0

    h.store(Event(name="test"))
    assert h.count() == 1
    assert len(h) == 1


def test_all():
    h = EventHistory()
    h.store(Event(name="a", payload=1))
    h.store(Event(name="b", payload=2))
    events = h.all()
    assert len(events) == 2
    assert [e.name for e in events] == ["a", "b"]


def test_latest():
    h = EventHistory()
    for i in range(5):
        h.store(Event(name=f"e{i}", payload=i))
    latest = h.latest(3)
    assert [e.name for e in latest] == ["e2", "e3", "e4"]


def test_latest_non_positive_limit():
    h = EventHistory()
    h.store(Event(name="a"))
    assert h.latest(0) == []
    assert h.latest(-1) == []


def test_clear():
    h = EventHistory()
    h.store(Event(name="a"))
    h.store(Event(name="b"))
    assert h.count() == 2
    h.clear()
    assert h.count() == 0


def test_max_events_retention():
    h = EventHistory(max_events=3)
    for i in range(5):
        h.store(Event(name=f"e{i}"))
    assert h.count() == 3
    assert [e.name for e in h.all()] == ["e2", "e3", "e4"]


def test_by_name():
    h = EventHistory()
    h.store(Event(name="user.login", payload={"u": 1}))
    h.store(Event(name="user.logout", payload={"u": 1}))
    h.store(Event(name="user.login", payload={"u": 2}))
    results = h.by_name("user.login")
    assert len(results) == 2
    assert all(e.name == "user.login" for e in results)


def test_by_source():
    h = EventHistory()
    h.store(Event(name="a", source="plugin:seo"))
    h.store(Event(name="b", source="kernel"))
    h.store(Event(name="c", source="plugin:seo"))
    results = h.by_source("plugin:seo")
    assert len(results) == 2


def test_iter():
    h = EventHistory()
    h.store(Event(name="a"))
    h.store(Event(name="b"))
    names = [e.name for e in h]
    assert names == ["a", "b"]


@pytest.mark.asyncio
async def test_replay_all():
    h = EventHistory()
    h.store(Event(name="a", payload=1))
    h.store(Event(name="b", payload=2))

    received = []

    async def publisher(event: Event) -> None:
        received.append((event.name, event.payload))

    await h.replay(publisher)
    assert received == [("a", 1), ("b", 2)]


@pytest.mark.asyncio
async def test_replay_topic():
    h = EventHistory()
    h.store(Event(name="user.login", payload={"u": 1}))
    h.store(Event(name="page.view", payload={"p": "/"}))
    h.store(Event(name="user.login", payload={"u": 2}))
    h.store(Event(name="user.logout", payload={"u": 1}))

    received = []

    async def publisher(event: Event) -> None:
        received.append(event.payload)

    await h.replay_topic("user.login", publisher)
    assert received == [{"u": 1}, {"u": 2}]


@pytest.mark.asyncio
async def test_replay_source():
    h = EventHistory()
    h.store(Event(name="a", source="plugin:seo"))
    h.store(Event(name="b", source="kernel"))
    h.store(Event(name="c", source="plugin:seo"))

    received = []

    async def publisher(event: Event) -> None:
        received.append(event.name)

    await h.replay_source("plugin:seo", publisher)
    assert received == ["a", "c"]


@pytest.mark.asyncio
async def test_replay_where():
    h = EventHistory()
    h.store(Event(name="a", payload=1))
    h.store(Event(name="b", payload=2))
    h.store(Event(name="c", payload=3))

    received = []

    async def publisher(event: Event) -> None:
        received.append(event.payload)

    await h.replay_where(lambda e: e.payload and e.payload > 1, publisher)
    assert received == [2, 3]


@pytest.mark.asyncio
async def test_replay_empty():
    h = EventHistory()
    received = []

    async def publisher(event: Event) -> None:
        received.append(event.name)

    await h.replay(publisher)
    assert received == []


@pytest.mark.asyncio
async def test_replay_maintains_order():
    h = EventHistory()
    for i in range(5):
        h.store(Event(name="t", payload=i))

    received = []

    async def publisher(event: Event) -> None:
        received.append(event.payload)

    await h.replay(publisher)
    assert received == [0, 1, 2, 3, 4]
