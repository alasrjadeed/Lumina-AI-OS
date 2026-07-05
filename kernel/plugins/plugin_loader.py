import importlib
import inspect
import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


@dataclass
class PluginManifest:
    name: str
    version: str
    description: str = ""
    author: str = ""
    dependencies: List[str] = field(default_factory=list)
    min_core_version: str = "1.0.0"
    entry_point: str = "main"
    permissions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginInfo:
    manifest: PluginManifest
    path: Path
    module: Any = None
    instance: Any = None
    is_loaded: bool = False
    error: Optional[str] = None


class PluginLoader:
    def __init__(self, plugin_dir: Optional[Path] = None):
        self._plugin_dir = plugin_dir or Path("./plugins")
        self._plugins: Dict[str, PluginInfo] = {}
        self._interfaces: Dict[str, Type] = {}

    def register_interface(self, name: str, interface_class: Type) -> None:
        self._interfaces[name] = interface_class
        logger.debug(f"Registered plugin interface: {name}")

    def discover(self, directory: Optional[Path] = None) -> List[PluginInfo]:
        scan_dir = directory or self._plugin_dir
        if not scan_dir.exists():
            logger.warning(f"Plugin directory does not exist: {scan_dir}")
            return []

        discovered: List[PluginInfo] = []
        for item in sorted(scan_dir.iterdir()):
            if not item.is_dir():
                continue
            manifest_file = item / "manifest.json"
            if not manifest_file.exists():
                continue

            try:
                manifest_data = json.loads(manifest_file.read_text())
                manifest = PluginManifest(**manifest_data)
                info = PluginInfo(manifest=manifest, path=item)
                self._plugins[manifest.name] = info
                discovered.append(info)
                logger.info(f"Discovered plugin: {manifest.name} v{manifest.version}")
            except Exception as e:
                logger.error(f"Failed to load manifest from {item}: {e}")

        return discovered

    def load(self, plugin_name: str) -> Optional[PluginInfo]:
        info = self._plugins.get(plugin_name)
        if not info:
            logger.error(f"Plugin '{plugin_name}' not found")
            return None
        if info.is_loaded:
            return info

        try:
            sys.path.insert(0, str(info.path))
            module = importlib.import_module(info.manifest.entry_point)
            info.module = module

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if inspect.isclass(attr) and hasattr(attr, "__plugin__"):
                    info.instance = attr()
                    break

            if info.instance is None:
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if inspect.isclass(attr):
                        for iface_name, iface_cls in self._interfaces.items():
                            if issubclass(attr, iface_cls) and attr is not iface_cls:
                                info.instance = attr()
                                break

            for dep in info.manifest.dependencies:
                if dep not in self._plugins or not self._plugins[dep].is_loaded:
                    self.load(dep)

            info.is_loaded = True
            logger.info(f"Loaded plugin: {plugin_name} v{info.manifest.version}")

            if info.instance and hasattr(info.instance, "on_load"):
                info.instance.on_load()

        except Exception as e:
            info.error = str(e)
            logger.exception(f"Failed to load plugin '{plugin_name}': {e}")
            return None

        return info

    def unload(self, plugin_name: str) -> bool:
        info = self._plugins.get(plugin_name)
        if not info or not info.is_loaded:
            return False

        try:
            if info.instance and hasattr(info.instance, "on_unload"):
                info.instance.on_unload()
            module_name = info.module.__name__ if info.module else ""
            if module_name in sys.modules:
                del sys.modules[module_name]
            if str(info.path) in sys.path:
                sys.path.remove(str(info.path))
            info.is_loaded = False
            info.instance = None
            info.module = None
            logger.info(f"Unloaded plugin: {plugin_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to unload plugin '{plugin_name}': {e}")
            return False

    def reload(self, plugin_name: str) -> Optional[PluginInfo]:
        self.unload(plugin_name)
        return self.load(plugin_name)

    def get_plugin(self, plugin_name: str) -> Optional[PluginInfo]:
        return self._plugins.get(plugin_name)

    def loaded_plugins(self) -> List[PluginInfo]:
        return [p for p in self._plugins.values() if p.is_loaded]

    def all_plugins(self) -> Dict[str, PluginInfo]:
        return dict(self._plugins)

    def get_instance(self, plugin_name: str) -> Optional[Any]:
        info = self._plugins.get(plugin_name)
        return info.instance if info and info.is_loaded else None

    def validate_dependencies(self, plugin_name: str) -> bool:
        info = self._plugins.get(plugin_name)
        if not info:
            return False
        for dep in info.manifest.dependencies:
            if dep not in self._plugins:
                logger.error(f"Plugin '{plugin_name}' missing dependency: {dep}")
                return False
        return True
