from __future__ import annotations

import contextlib
import importlib
import inspect
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from core.log import log


@dataclass
class PluginMetadata:
    name: str
    version: str = "0.1.0"
    description: str = ""
    author: str = ""
    dependencies: list[str] = field(default_factory=list)
    hooks: list[str] = field(default_factory=list)


class Plugin(Protocol):
    metadata: PluginMetadata

    def on_load(self) -> None: ...
    def on_unload(self) -> None: ...
    def on_enable(self) -> None: ...
    def on_disable(self) -> None: ...


@dataclass
class PluginInfo:
    metadata: PluginMetadata
    enabled: bool = True
    loaded: bool = False
    module: Any = None
    instance: Any = None
    path: str = ""


class PluginManager:
    """Discover, load, and manage plugins with lifecycle hooks."""

    def __init__(self, plugin_dirs: list[str] | None = None):
        self._plugins: dict[str, PluginInfo] = {}
        self._hooks: dict[str, list[Callable]] = {}
        self._plugin_dirs = plugin_dirs or []
        if not plugin_dirs:
            default = self._get_default_dir()
            if default not in self._plugin_dirs:
                self._plugin_dirs.append(default)

    def _get_default_dir(self) -> str:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, "plugins")

    def discover(self, directory: str = "") -> list[str]:
        found = []
        search_dirs = [directory] if directory else self._plugin_dirs
        for d in search_dirs:
            if not os.path.isdir(d):
                continue
            for entry in os.listdir(d):
                plugin_path = os.path.join(d, entry)
                if os.path.isdir(plugin_path) and os.path.exists(
                    os.path.join(plugin_path, "__init__.py"),
                ) or entry.endswith(".py") and entry != "__init__.py":
                    found.append(plugin_path)
        return found

    def load(self, name: str, path: str = "") -> bool:
        if name in self._plugins:
            log.warning("Plugin already loaded: %s", name)
            return False
        plugin_path = path or self._find_plugin_path(name)
        if not plugin_path:
            log.warning("Plugin not found: %s", name)
            return False
        try:
            if os.path.isdir(plugin_path):
                spec = importlib.util.spec_from_file_location(
                    name, os.path.join(plugin_path, "__init__.py"),
                )
            else:
                spec = importlib.util.spec_from_file_location(name, plugin_path)
            if not spec or not spec.loader:
                return False
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            instance = self._instantiate(module)
            metadata = self._extract_metadata(module, instance, name)
            info = PluginInfo(
                metadata=metadata,
                loaded=True,
                module=module,
                instance=instance,
                path=plugin_path,
            )
            self._plugins[name] = info
            if instance and hasattr(instance, "on_load"):
                instance.on_load()
            for hook in metadata.hooks:
                self._register_hook_method(name, instance, hook)
            log.info("Plugin loaded: %s v%s", name, metadata.version)
            return True
        except Exception as e:
            log.error("Failed to load plugin %s: %s", name, e)
            return False

    def unload(self, name: str) -> bool:
        info = self._plugins.pop(name, None)
        if not info:
            return False
        if info.instance and hasattr(info.instance, "on_unload"):
            with contextlib.suppress(Exception):
                info.instance.on_unload()
        self._remove_hooks(name)
        sys.modules.pop(name, None)
        log.info("Plugin unloaded: %s", name)
        return True

    def enable(self, name: str) -> bool:
        info = self._plugins.get(name)
        if not info:
            return False
        info.enabled = True
        if info.instance and hasattr(info.instance, "on_enable"):
            info.instance.on_enable()
        return True

    def disable(self, name: str) -> bool:
        info = self._plugins.get(name)
        if not info:
            return False
        info.enabled = False
        if info.instance and hasattr(info.instance, "on_disable"):
            info.instance.on_disable()
        return True

    def is_loaded(self, name: str) -> bool:
        return name in self._plugins

    def is_enabled(self, name: str) -> bool:
        info = self._plugins.get(name)
        return info is not None and info.enabled

    def get_plugin(self, name: str) -> PluginInfo | None:
        return self._plugins.get(name)

    def list_plugins(self, enabled_only: bool = False) -> list[PluginInfo]:
        if enabled_only:
            return [p for p in self._plugins.values() if p.enabled]
        return list(self._plugins.values())

    def register_hook(self, hook: str, callback: Callable) -> None:
        self._hooks.setdefault(hook, []).append(callback)

    def trigger_hook(self, hook: str, *args: Any, **kwargs: Any) -> list[Any]:
        results = []
        for callback in self._hooks.get(hook, []):
            try:
                results.append(callback(*args, **kwargs))
            except Exception as e:
                log.error("Hook '%s' error: %s", hook, e)
        return results

    def _find_plugin_path(self, name: str) -> str:
        for d in self._plugin_dirs:
            dir_path = os.path.join(d, name)
            if os.path.isdir(dir_path):
                return dir_path
            file_path = os.path.join(d, f"{name}.py")
            if os.path.isfile(file_path):
                return file_path
        return ""

    def _instantiate(self, module) -> Any:
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and not name.startswith("_") and obj.__module__ != "typing":
                try:
                    return obj()
                except Exception:
                    continue
        return None

    def _extract_metadata(self, module, instance: Any, name: str) -> PluginMetadata:
        if instance and hasattr(instance, "metadata"):
            return instance.metadata
        metadata = getattr(module, "metadata", None)
        if isinstance(metadata, PluginMetadata):
            return metadata
        return PluginMetadata(name=name)

    def _register_hook_method(self, name: str, instance: Any, hook: str) -> None:
        method = getattr(instance, f"on_{hook}", None)
        if method:
            self.register_hook(hook, method)

    def _remove_hooks(self, name: str) -> None:
        for hook in list(self._hooks.keys()):
            self._hooks[hook] = [
                cb for cb in self._hooks[hook]
                if not (hasattr(cb, "__self__") and getattr(cb.__self__, "__module__", "") == name)
            ]

    def load_all(self, directory: str = "") -> int:
        count = 0
        for path in self.discover(directory):
            name = os.path.splitext(os.path.basename(path))[0]
            if self.load(name, path):
                count += 1
        return count

    def unload_all(self) -> int:
        count = 0
        for name in list(self._plugins.keys()):
            if self.unload(name):
                count += 1
        return count
