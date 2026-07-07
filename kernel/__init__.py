import contextlib

from kernel.dependency import DIContainer
from kernel.dependency.lifetime import Lifetime
from kernel.events import (
    DLQBackend,
    DuplicateSubscriberError,
    Event,
    EventSubscriberError,
    EventValidationError,
    InvalidEventError,
    Priority,
    Publisher,
    SqliteDeadLetterQueue,
    Subscriber,
    Subscription,
)
from kernel.events.builtins import (
    LoggingMiddleware,
    MetricsMiddleware,
    OpenTelemetryMiddleware,
    RateLimitMiddleware,
    TracingMiddleware,
    ValidationMiddleware,
)
from kernel.events.event_bus import EventBus
from kernel.interfaces import IEvent, IPlugin, IPublisher, IService, ISubscriber
from kernel.log import setup_log
from kernel.models import Job, JobStatus, PluginManifest, PluginStatus, PluginType
from kernel.plugins.loader import PluginLoader as _PluginLoader
from kernel.plugins.registry import PluginRegistry
from kernel.plugins.sandbox import SandboxedPlugin, SandboxedPluginLoader
from kernel.plugins.version import SemVer, check_plugin_compatibility, version_matches
from kernel.scheduler.scheduler import Scheduler
from kernel.services.registry import ServiceRegistry as _ServiceRegistry

__all__ = [
    "event_bus", "services", "di", "plugins", "scheduler", "Kernel",
    "Event", "Subscriber", "Publisher", "Subscription", "Priority",
    "IEvent", "ISubscriber", "IPublisher", "IService", "IPlugin",
    "Lifetime", "Job", "JobStatus", "PluginManifest", "PluginStatus",
    "setup_log",
    "DuplicateSubscriberError", "InvalidEventError",
    "EventValidationError", "EventSubscriberError",
    "LoggingMiddleware",
    "MetricsMiddleware",
    "ValidationMiddleware",
    "TracingMiddleware",
    "RateLimitMiddleware",
    "OpenTelemetryMiddleware",
    "PluginRegistry",
    "SandboxedPlugin",
    "SandboxedPluginLoader",
    "SemVer",
    "version_matches",
    "check_plugin_compatibility",
    "PluginType",
    "DLQBackend",
    "SqliteDeadLetterQueue",
]


class Kernel:
    def __init__(self, use_globals: bool = True):
        if use_globals:
            self.event_bus = event_bus
            self.services = services
            self.di = di
            self.plugins = plugins
            self.scheduler = scheduler
        else:
            fresh_di = DIContainer()
            fresh_event_bus = EventBus(container=fresh_di)
            fresh_services = _ServiceRegistry(container=fresh_di)
            fresh_plugins = _PluginLoader(container=fresh_di)
            fresh_scheduler = Scheduler(container=fresh_di)
            fresh_di.register_instance("event_bus", fresh_event_bus)
            fresh_di.register_instance("services", fresh_services)
            fresh_di.register_instance("plugins", fresh_plugins)
            fresh_di.register_instance("scheduler", fresh_scheduler)
            self.event_bus = fresh_event_bus
            self.services = fresh_services
            self.di = fresh_di
            self.plugins = fresh_plugins
            self.scheduler = fresh_scheduler
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
        if not self._initialized:
            return
        with contextlib.suppress(RuntimeError):
            await self.event_bus.publish(Event(name="kernel.shutdown", payload={}))
        await self.scheduler.stop()
        await self.event_bus.shutdown()
        self._initialized = False


# Module-level convenience singletons
di = DIContainer()
event_bus = EventBus(container=di)
services = _ServiceRegistry(container=di)
plugins = _PluginLoader(container=di)
scheduler = Scheduler(container=di)

di.register_instance("event_bus", event_bus)
di.register_instance("services", services)
di.register_instance("plugins", plugins)
di.register_instance("scheduler", scheduler)
