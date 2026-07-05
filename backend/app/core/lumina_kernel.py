import logging
from typing import Any, Dict, Optional

from kernel import EventBus, Scheduler, ServiceRegistry, DIContainer, PluginLoader

logger = logging.getLogger(__name__)


class LuminaKernel:
    def __init__(self):
        self.event_bus = EventBus()
        self.scheduler = Scheduler()
        self.service_registry = ServiceRegistry()
        self.di_container = DIContainer()
        self.plugin_loader = PluginLoader()
        self._initialized = False

    async def initialize(self):
        self.di_container.register_instance("event_bus", self.event_bus)
        self.di_container.register_instance("scheduler", self.scheduler)
        self.di_container.register_instance("service_registry", self.service_registry)
        self.di_container.register_instance("plugin_loader", self.plugin_loader)

        await self.scheduler.start()
        self._initialized = True
        logger.info("Lumina Kernel initialized")

    async def shutdown(self):
        await self.scheduler.stop()
        self._initialized = False
        logger.info("Lumina Kernel shutdown")

    def get_status(self) -> Dict[str, Any]:
        return {
            "initialized": self._initialized,
            "services": self.service_registry.get_service_count(),
            "pending_jobs": self.scheduler.pending_count(),
            "events_in_history": self.event_bus.event_count(),
            "plugins_loaded": len(self.plugin_loader.loaded_plugins()),
        }
