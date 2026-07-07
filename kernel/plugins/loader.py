from __future__ import annotations

import contextlib
import importlib
import inspect
import json
import os
import sys
from typing import Any

from kernel.events import Event
from kernel.events.subscription import Subscription
from kernel.exceptions import PluginLoadError
from kernel.interfaces.plugin_interface import IPlugin
from kernel.log import setup_log
from kernel.models import PluginManifest, PluginStatus, PluginType

log = setup_log("plugins")


class PluginLoader:
    def __init__(
        self,
        plugin_dirs: list[str] | None = None,
        container: Any | None = None,
    ):
        self._container = container
        self._plugins: dict[str, Any] = {}
        self._manifests: dict[str, PluginManifest] = {}
        self._statuses: dict[str, PluginStatus] = {}
        self._plugin_dirs = plugin_dirs or []
        self._event_bus: Any = None
        self._tracked_subs: dict[str, list[Subscription]] = {}
        if container is not None:
            self._event_bus = container.try_resolve("event_bus")

    def add_plugin_dir(self, path: str) -> None:
        if path not in self._plugin_dirs:
            self._plugin_dirs.append(path)

    async def discover(self) -> None:
        for plugin_dir in self._plugin_dirs:
            if not os.path.isdir(plugin_dir):
                continue
            for entry in sorted(os.listdir(plugin_dir)):
                plugin_path = os.path.join(plugin_dir, entry)
                if os.path.isdir(plugin_path) and os.path.exists(
                    os.path.join(plugin_path, "__init__.py"),
                ):
                    try:
                        self._discover_plugin_dir(plugin_path, entry)
                    except Exception as e:
                        log.warning("Skipped plugin '%s': %s", entry, e)

    def _discover_plugin_dir(self, path: str, name: str) -> None:
        manifest_path = os.path.join(path, "manifest.json")
        manifest = PluginManifest(name=name, version="0.1.0")
        if os.path.exists(manifest_path):
            with open(manifest_path) as f:
                data = json.load(f)
            pt_str = data.get("plugin_type", "")
            plugin_type = PluginType.STANDARD
            if pt_str:
                with contextlib.suppress(ValueError):
                    plugin_type = PluginType(pt_str)
            manifest = PluginManifest(
                name=data.get("name", name),
                version=data.get("version", "0.1.0"),
                description=data.get("description", ""),
                author=data.get("author", ""),
                homepage=data.get("homepage", ""),
                license=data.get("license", ""),
                dependencies=data.get("dependencies", []),
                entry_point=data.get("entry_point", "main"),
                tags=data.get("tags", []),
                plugin_type=plugin_type,
                version_requirements=data.get("version_requirements", {}),
                python_version=data.get("python_version", ">=3.10"),
                kernel_version=data.get("kernel_version", ">=0.1.0"),
            )

        if manifest.name in self._plugins or manifest.name in self._manifests:
            raise PluginLoadError(name, "Already discovered")

        self._manifests[manifest.name] = manifest
        self._statuses[manifest.name] = PluginStatus.DISCOVERED
        log.info("Discovered plugin: %s v%s", manifest.name, manifest.version)

    async def load(self, name: str) -> Any:
        if name in self._plugins:
            return self._plugins[name]

        manifest = self._manifests.get(name)
        if not manifest:
            raise PluginLoadError(name, "Not discovered")

        for dep in manifest.dependencies:
            if dep not in self._plugins:
                await self.load(dep)

        for plugin_dir in self._plugin_dirs:
            plugin_path = os.path.join(plugin_dir, name)
            if os.path.isdir(plugin_path):
                if plugin_path not in sys.path:
                    sys.path.insert(0, os.path.dirname(plugin_path))
                try:
                    module = importlib.import_module(name)
                    if not hasattr(module, manifest.entry_point):
                        raise PluginLoadError(name, "Entry point not found")

                    plugin_cls = getattr(module, manifest.entry_point)
                    plugin_instance: Any = plugin_cls
                    if inspect.isclass(plugin_cls):
                        try:
                            plugin_instance = plugin_cls(container=self._container)
                        except TypeError:
                            plugin_instance = plugin_cls()

                    if isinstance(plugin_instance, IPlugin):
                        await plugin_instance.on_load(self._container)
                        await self._auto_subscribe(name, plugin_instance)

                    self._plugins[name] = plugin_instance
                    self._statuses[name] = PluginStatus.LOADED
                    await self._emit("plugin.loaded", name)
                    log.info("Loaded plugin: %s", name)
                    return plugin_instance
                except Exception as e:
                    self._statuses[name] = PluginStatus.ERROR
                    if not isinstance(e, PluginLoadError):
                        raise PluginLoadError(name, str(e)) from e
                    raise

        raise PluginLoadError(name, "Plugin directory not found")

    async def unload(self, name: str) -> None:
        if name not in self._plugins:
            raise PluginLoadError(name, "Not loaded")
        plugin = self._plugins[name]
        await self._auto_unsubscribe(name)
        if isinstance(plugin, IPlugin):
            await plugin.on_unload()
        del self._plugins[name]
        self._statuses[name] = PluginStatus.DISCOVERED
        await self._emit("plugin.unloaded", name)
        log.info("Unloaded plugin: %s", name)

    async def _auto_subscribe(self, name: str, plugin: IPlugin) -> None:
        subs = list(plugin.subscriptions)
        if not subs or self._event_bus is None:
            return
        topic_ids: list[str] = []
        for sub in subs:
            try:
                await self._event_bus.register(sub)
                topic_ids.append(f"{sub.topic}:{sub.subscription_id}")
            except Exception:
                log.warning("Failed to subscribe plugin '%s' to %s", name, sub.topic)
        self._tracked_subs[name] = subs
        log.info("Plugin '%s' subscribed to %d topics", name, len(subs))

    async def _auto_unsubscribe(self, name: str) -> None:
        subs = self._tracked_subs.pop(name, None)
        if not subs or self._event_bus is None:
            return
        for sub in subs:
            with contextlib.suppress(Exception):
                await self._event_bus.unregister(sub.topic, sub.handler)

    async def subscribe_to(self, name: str, topic: str, handler: Any) -> bool:
        if name not in self._plugins or self._event_bus is None:
            return False
        sub = Subscription(topic=topic, handler=handler)
        try:
            await self._event_bus.register(sub)
            self._tracked_subs.setdefault(name, []).append(sub)
            return True
        except Exception:
            return False

    async def enable(self, name: str) -> None:
        if name not in self._plugins:
            plugin = await self.load(name)
        plugin = self._plugins.get(name)
        if not plugin:
            raise PluginLoadError(name, "Not loaded")
        if isinstance(plugin, IPlugin):
            await plugin.on_enable()
        self._statuses[name] = PluginStatus.ENABLED
        await self._emit("plugin.enabled", name)
        log.info("Enabled plugin: %s", name)

    async def disable(self, name: str) -> None:
        if name not in self._plugins:
            raise PluginLoadError(name, "Not loaded")
        plugin = self._plugins[name]
        if isinstance(plugin, IPlugin):
            await plugin.on_disable()
        self._statuses[name] = PluginStatus.DISABLED
        await self._emit("plugin.disabled", name)
        log.info("Disabled plugin: %s", name)

    async def install(self, name: str) -> None:
        if name in self._plugins:
            return
        manifest = self._manifests.get(name)
        if not manifest:
            raise PluginLoadError(name, "Not discovered")
        plugin = await self.load(name)
        if isinstance(plugin, IPlugin):
            await plugin.on_install()
        await self._emit("plugin.installed", name)

    async def uninstall(self, name: str) -> None:
        if name not in self._plugins:
            raise PluginLoadError(name, "Not loaded")
        plugin = self._plugins[name]
        if isinstance(plugin, IPlugin):
            await plugin.on_uninstall()
        await self.unload(name)
        self._statuses.pop(name, None)
        self._manifests.pop(name, None)
        await self._emit("plugin.uninstalled", name)
        log.info("Uninstalled plugin: %s", name)

    def get_status(self, name: str) -> PluginStatus | None:
        return self._statuses.get(name)

    def get_manifest(self, name: str) -> PluginManifest | None:
        return self._manifests.get(name)

    def list_loaded(self) -> list[str]:
        return list(self._plugins.keys())

    def list_discovered(self) -> list[PluginManifest]:
        return list(self._manifests.values())

    def list_by_status(self, status: PluginStatus) -> list[str]:
        return [n for n, s in self._statuses.items() if s == status]

    def find_by_tag(self, tag: str) -> list[PluginManifest]:
        return [m for m in self._manifests.values() if tag in m.tags]

    async def reload(self, name: str) -> Any:
        if name not in self._plugins:
            raise PluginLoadError(name, "Not loaded")
        for mod_name in list(sys.modules.keys()):
            if mod_name == name or mod_name.startswith(f"{name}."):
                del sys.modules[mod_name]
        await self.unload(name)
        return await self.load(name)

    async def _emit(self, event_name: str, plugin_name: str) -> None:
        if self._event_bus is None:
            return
        with contextlib.suppress(Exception):
            await self._event_bus.publish(
                Event(
                    name=f"plugin.{event_name}",
                    payload={"plugin": plugin_name},
                    source="plugins",
                ),
            )
