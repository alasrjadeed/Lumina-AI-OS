import importlib
import inspect
import os
import sys
from typing import Any

from kernel.log import setup_log
from kernel.models import PluginManifest
from kernel.exceptions import PluginLoadError

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
        self._plugin_dirs = plugin_dirs or []

    def add_plugin_dir(self, path: str):
        if path not in self._plugin_dirs:
            self._plugin_dirs.append(path)

    async def discover(self):
        for plugin_dir in self._plugin_dirs:
            if not os.path.isdir(plugin_dir):
                continue
            for entry in os.listdir(plugin_dir):
                plugin_path = os.path.join(plugin_dir, entry)
                if os.path.isdir(plugin_path) and os.path.exists(os.path.join(plugin_path, "__init__.py")):
                    try:
                        self._load_plugin_dir(plugin_path, entry)
                    except Exception as e:
                        log.warning("Skipped plugin '%s': %s", entry, e)

    def _load_plugin_dir(self, path: str, name: str):
        manifest_path = os.path.join(path, "manifest.json")
        manifest = PluginManifest(name=name, version="0.1.0")
        if os.path.exists(manifest_path):
            import json
            with open(manifest_path) as f:
                data = json.load(f)
                manifest = PluginManifest(
                    name=data.get("name", name),
                    version=data.get("version", "0.1.0"),
                    description=data.get("description", ""),
                    author=data.get("author", ""),
                    dependencies=data.get("dependencies", []),
                    entry_point=data.get("entry_point", "main"),
                )

        if manifest.name in self._plugins:
            raise PluginLoadError(name, "Already loaded")

        self._manifests[manifest.name] = manifest
        log.info("Discovered plugin: %s v%s", manifest.name, manifest.version)

    def load(self, name: str) -> Any:
        if name in self._plugins:
            return self._plugins[name]

        manifest = self._manifests.get(name)
        if not manifest:
            raise PluginLoadError(name, "Not discovered")

        for dep in manifest.dependencies:
            if dep not in self._plugins:
                self.load(dep)

        for plugin_dir in self._plugin_dirs:
            plugin_path = os.path.join(plugin_dir, name)
            if os.path.isdir(plugin_path):
                if plugin_path not in sys.path:
                    sys.path.insert(0, os.path.dirname(plugin_path))
                try:
                    module = importlib.import_module(name)
                    if hasattr(module, manifest.entry_point):
                        plugin_instance = getattr(module, manifest.entry_point)
                        if inspect.isclass(plugin_instance):
                            try:
                                plugin_instance = plugin_instance(container=self._container)
                            except TypeError:
                                plugin_instance = plugin_instance()
                        self._plugins[name] = plugin_instance
                        log.info("Loaded plugin: %s", name)
                        return plugin_instance
                except Exception as e:
                    raise PluginLoadError(name, str(e)) from e

        raise PluginLoadError(name, "Entry point not found")

    def unload(self, name: str):
        if name in self._plugins:
            del self._plugins[name]
            log.info("Unloaded plugin: %s", name)

    def list_loaded(self) -> list[str]:
        return list(self._plugins.keys())

    def list_discovered(self) -> list[PluginManifest]:
        return list(self._manifests.values())
