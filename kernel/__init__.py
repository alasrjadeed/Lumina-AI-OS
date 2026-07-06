from kernel.events.event_bus import EventBus
from kernel.events import (
    Event,
    Subscriber,
    Publisher,
    Subscription,
    Priority,
    DuplicateSubscriberError,
    InvalidEventError,
    EventValidationError,
    EventSubscriberError,
)
from kernel.services.registry import ServiceRegistry
from kernel.dependency import DIContainer
from kernel.dependency.lifetime import Lifetime
from kernel.plugins.loader import PluginLoader
from kernel.scheduler.scheduler import Scheduler
from kernel.interfaces import IEvent, ISubscriber, IPublisher, IService
from kernel.log import setup_log

di = DIContainer()
event_bus = EventBus(container=di)
services = ServiceRegistry(container=di)
plugins = PluginLoader(container=di)
scheduler = Scheduler(container=di)

di.register_instance("event_bus", event_bus)
di.register_instance("services", services)
di.register_instance("plugins", plugins)
di.register_instance("scheduler", scheduler)

__all__ = [
    "event_bus", "services", "di", "plugins", "scheduler", "Kernel",
    "Event", "Subscriber", "Publisher", "Subscription", "Priority",
    "IEvent", "ISubscriber", "IPublisher", "IService",
    "DuplicateSubscriberError", "InvalidEventError",
    "EventValidationError", "EventSubscriberError",
]


class Kernel:
    def __init__(self):
        self.event_bus = event_bus
        self.services = services
        self.di = di
        self.plugins = plugins
        self.scheduler = scheduler
        self._initialized = False

    async def init(self):
        if self._initialized:
            return
        await self.plugins.discover()
        self.event_bus.start()
        await self.scheduler.start()
        self._initialized = True
        await self.event_bus.publish(Event(name="kernel.initialized", payload={}))

    async def shutdown(self):
        await self.event_bus.publish(Event(name="kernel.shutdown", payload={}))
        await self.scheduler.stop()
        await self.event_bus.shutdown()
        self._initialized = False
