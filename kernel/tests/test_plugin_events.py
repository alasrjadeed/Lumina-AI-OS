import pytest

from kernel.dependency import DIContainer
from kernel.events.event import Event
from kernel.events.event_bus import EventBus
from kernel.plugins.loader import PluginLoader


@pytest.mark.asyncio
async def test_plugin_subscriptions_auto_registered_on_load(tmp_path):

    container = DIContainer()
    bus = EventBus(container=container)
    container.register_instance("event_bus", bus)
    bus.start()

    plugin_dir = tmp_path / "sub_plugin"
    plugin_dir.mkdir()
    (plugin_dir / "__init__.py").write_text(
        "from kernel.interfaces.plugin_interface import IPlugin\n"
        "from kernel.events.subscription import Subscription\n"
        "class SubPlugin(IPlugin):\n"
        "    def __init__(self, container=None):\n"
        "        self.container = container\n"
        "        self.events = []\n"
        "    async def on_load(self, container=None):\n"
        "        pass\n"
        "    async def on_unload(self):\n"
        "        pass\n"
        "    @property\n"
        "    def subscriptions(self):\n"
        "        async def handler(event):\n"
        "            self.events.append(event.name)\n"
        "        return [Subscription(topic='test.*', handler=handler)]\n"
        "main = SubPlugin\n",
    )

    loader = PluginLoader(plugin_dirs=[str(tmp_path)], container=container)
    await loader.discover()
    plugin = await loader.load("sub_plugin")

    assert bus.has_subscribers("test.*")

    await bus.publish(Event(name="test.hello", payload={}, source="test"))
    await bus.join()

    assert "test.hello" in plugin.events


@pytest.mark.asyncio
async def test_plugin_subscriptions_unsubscribed_on_unload(tmp_path):

    container = DIContainer()
    bus = EventBus(container=container)
    container.register_instance("event_bus", bus)
    bus.start()

    plugin_dir = tmp_path / "unsub_plugin"
    plugin_dir.mkdir()
    (plugin_dir / "__init__.py").write_text(
        "from kernel.interfaces.plugin_interface import IPlugin\n"
        "from kernel.events.subscription import Subscription\n"
        "class UnsubPlugin(IPlugin):\n"
        "    def __init__(self, container=None):\n"
        "        pass\n"
        "    async def on_load(self, container=None):\n"
        "        pass\n"
        "    async def on_unload(self):\n"
        "        pass\n"
        "    @property\n"
        "    def subscriptions(self):\n"
        "        async def handler(event):\n"
        "            pass\n"
        "        return [Subscription(topic='unsub.*', handler=handler)]\n"
        "main = UnsubPlugin\n",
    )

    loader = PluginLoader(plugin_dirs=[str(tmp_path)], container=container)
    await loader.discover()
    await loader.load("unsub_plugin")
    assert bus.has_subscribers("unsub.*")

    await loader.unload("unsub_plugin")
    assert not bus.has_subscribers("unsub.*")


@pytest.mark.asyncio
async def test_subscribe_to_helper(tmp_path):

    container = DIContainer()
    bus = EventBus(container=container)
    container.register_instance("event_bus", bus)
    bus.start()

    plugin_dir = tmp_path / "helper_plugin"
    plugin_dir.mkdir()
    (plugin_dir / "__init__.py").write_text(
        "class main:\n    pass\n",
    )

    results = []

    async def handler(event):
        results.append(event.name)

    loader = PluginLoader(plugin_dirs=[str(tmp_path)], container=container)
    await loader.discover()
    await loader.load("helper_plugin")

    ok = await loader.subscribe_to("helper_plugin", "helper.topic", handler)
    assert ok is True

    await bus.publish(Event(name="helper.topic", payload={}, source="test"))
    await bus.join()
    assert "helper.topic" in results


@pytest.mark.asyncio
async def test_plugin_no_subscriptions_does_nothing(tmp_path):

    container = DIContainer()
    bus = EventBus(container=container)
    container.register_instance("event_bus", bus)
    bus.start()

    plugin_dir = tmp_path / "nosub"
    plugin_dir.mkdir()
    (plugin_dir / "__init__.py").write_text(
        "from kernel.interfaces.plugin_interface import IPlugin\n"
        "class NoSubPlugin(IPlugin):\n"
        "    def __init__(self, container=None):\n"
        "        pass\n"
        "    async def on_load(self, container=None):\n"
        "        pass\n"
        "    async def on_unload(self):\n"
        "        pass\n"
        "main = NoSubPlugin\n",
    )

    loader = PluginLoader(plugin_dirs=[str(tmp_path)], container=container)
    await loader.discover()
    await loader.load("nosub")
    # No subscriptions should be registered — nothing to assert, just no crash
    assert True
