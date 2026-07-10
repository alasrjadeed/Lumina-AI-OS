from __future__ import annotations

from collections import defaultdict
from typing import Any

from kernel.exceptions import (
    CircularDependencyError,
    PluginDependencyError,
    PluginLoadError,
    PluginNotDiscoveredError,
)
from kernel.log import setup_log
from kernel.models import PluginManifest, PluginStatus, PluginType
from kernel.plugins.loader import PluginLoader
from kernel.plugins.version import SemVer, check_plugin_compatibility, version_matches

log = setup_log("plugins.registry")


class PluginRegistry:
    def __init__(
        self,
        loader: PluginLoader | None = None,
        plugin_dirs: list[str] | None = None,
    ) -> None:
        if loader is not None:
            self._loader = loader
        elif plugin_dirs is not None:
            self._loader = PluginLoader(plugin_dirs=plugin_dirs)
        else:
            self._loader = PluginLoader()
        self._dependency_graph: dict[str, set[str]] = defaultdict(set)

    # ------------------------------------------------------------------
    # Delegation to PluginLoader
    # ------------------------------------------------------------------

    @property
    def loader(self) -> PluginLoader:
        return self._loader

    def add_plugin_dir(self, path: str) -> None:
        self._loader.add_plugin_dir(path)

    async def discover(self) -> list[PluginManifest]:
        await self._loader.discover()
        self._rebuild_dependency_graph()
        return self._loader.list_discovered()

    async def load(self, name: str) -> Any:
        manifest = self._loader.get_manifest(name)
        if manifest is None:
            raise PluginNotDiscoveredError(name)

        errors = self._check_version_compatibility(name)
        if errors:
            for e in errors:
                log.error(e)
            raise PluginDependencyError(name, errors)

        for dep in manifest.dependencies:
            dep_manifest = self._loader.get_manifest(dep)
            if dep_manifest is None:
                raise PluginDependencyError(name, [f"dependency '{dep}' not discovered"])
            if dep not in self._loader._plugins:
                await self.load(dep)

        return await self._loader.load(name)

    async def unload(self, name: str) -> None:
        dependents = self._get_dependents(name)
        if dependents:
            raise PluginLoadError(
                name,
                f"Cannot unload: still required by {', '.join(dependents)}",
            )
        await self._loader.unload(name)

    async def enable(self, name: str) -> None:
        await self._loader.enable(name)

    async def disable(self, name: str) -> None:
        await self._loader.disable(name)

    async def install(self, name: str) -> Any:
        return await self._loader.install(name)

    async def uninstall(self, name: str) -> None:
        dependents = self._get_dependents(name)
        if dependents:
            raise PluginLoadError(
                name,
                f"Cannot uninstall: still required by {', '.join(dependents)}",
            )
        await self._loader.uninstall(name)

    async def subscribe_to(self, name: str, topic: str, handler: Any) -> bool:
        return await self._loader.subscribe_to(name, topic, handler)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_manifest(self, name: str) -> PluginManifest | None:
        return self._loader.get_manifest(name)

    def get_status(self, name: str) -> PluginStatus | None:
        return self._loader.get_status(name)

    def list_loaded(self) -> list[str]:
        return self._loader.list_loaded()

    def list_discovered(self) -> list[PluginManifest]:
        return self._loader.list_discovered()

    def list_by_status(self, status: PluginStatus) -> list[str]:
        return self._loader.list_by_status(status)

    def find_by_tag(self, tag: str) -> list[PluginManifest]:
        return self._loader.find_by_tag(tag)

    def find_by_type(self, plugin_type: PluginType) -> list[PluginManifest]:
        return [m for m in self._loader.list_discovered() if m.plugin_type == plugin_type]

    def find_by_author(self, author: str) -> list[PluginManifest]:
        return [m for m in self._loader.list_discovered() if m.author.lower() == author.lower()]

    def search(self, query: str) -> list[PluginManifest]:
        q = query.lower()
        return [
            m
            for m in self._loader.list_discovered()
            if q in m.name.lower()
            or q in m.description.lower()
            or q in m.author.lower()
            or any(q in t.lower() for t in m.tags)
        ]

    # ------------------------------------------------------------------
    # Version queries
    # ------------------------------------------------------------------

    def get_version(self, name: str) -> SemVer | None:
        manifest = self._loader.get_manifest(name)
        if manifest is None:
            return None
        try:
            return SemVer.parse(manifest.version)
        except ValueError:
            return None

    def list_outdated(self) -> list[tuple[str, str]]:
        outdated: list[tuple[str, str]] = []
        for manifest in self._loader.list_discovered():
            for dep_name, spec in manifest.version_requirements.items():
                dep_manifest = self._loader.get_manifest(dep_name)
                if dep_manifest is None:
                    continue
                try:
                    dv = SemVer.parse(dep_manifest.version)
                except ValueError:
                    continue
                if not version_matches(spec, dv):
                    outdated.append((manifest.name, dep_name))
        return outdated

    def list_by_kernel_version(self, kernel_spec: str) -> list[PluginManifest]:
        kv = SemVer.parse(kernel_spec.replace(">=", "").replace("==", "").strip())
        return [m for m in self._loader.list_discovered() if version_matches(m.kernel_version, kv)]

    def list_incompatible_plugins(self) -> list[str]:
        incompatible: list[str] = []
        for manifest in self._loader.list_discovered():
            errors = check_plugin_compatibility(
                manifest.name,
                manifest.version,
                manifest.version_requirements,
                self._all_versions(),
            )
            if errors:
                incompatible.append(manifest.name)
        return incompatible

    # ------------------------------------------------------------------
    # Dependency graph
    # ------------------------------------------------------------------

    def get_dependencies(self, name: str) -> list[str]:
        manifest = self._loader.get_manifest(name)
        if manifest is None:
            return []
        return list(manifest.dependencies)

    def get_dependents(self, name: str) -> list[str]:
        return sorted(self._get_dependents(name))

    def dependency_chain(self, name: str) -> list[list[str]]:
        manifest = self._loader.get_manifest(name)
        if manifest is None:
            return []
        result: list[list[str]] = []
        seen: set[str] = set()

        def _walk(current: str, path: list[str]) -> None:
            if current in seen:
                return
            seen.add(current)
            m = self._loader.get_manifest(current)
            if m is None:
                return
            if not m.dependencies:
                result.append(path + [current])
                return
            for dep in m.dependencies:
                _walk(dep, path + [current])

        _walk(name, [])
        return result

    def load_order(self) -> list[str]:
        visited: set[str] = set()
        order: list[str] = []
        manifests = {m.name: m for m in self._loader.list_discovered()}

        def _visit(name: str, path: set[str]) -> None:
            if name in visited:
                return
            if name in path:
                raise CircularDependencyError(list(path) + [name])
            m = manifests.get(name)
            if m is None:
                return
            path.add(name)
            for dep in m.dependencies:
                _visit(dep, path)
            path.remove(name)
            visited.add(name)
            order.append(name)

        for name in manifests:
            _visit(name, set())
        return order

    # ------------------------------------------------------------------
    # Hot reload
    # ------------------------------------------------------------------

    async def reload(self, name: str, cascade: bool = False) -> Any:
        if cascade:
            return await self._cascade_reload(name)
        return await self._loader.reload(name)

    async def reload_all(self) -> dict[str, Any]:
        results: dict[str, Any] = {}
        for name in self.list_loaded():
            try:
                results[name] = await self._loader.reload(name)
            except Exception as e:
                results[name] = e
        return results

    async def _cascade_reload(self, name: str) -> Any:
        order = self.load_order()
        to_reload: list[str] = []
        started = False
        for p in order:
            if p == name:
                started = True
            if started or name in (self.get_dependencies(p) or []):
                to_reload.append(p)

        to_reload = list(dict.fromkeys(to_reload))
        if name not in to_reload:
            to_reload.append(name)

        result: Any = None
        for plugin_name in to_reload:
            if plugin_name in self._loader._plugins:
                try:
                    result = await self._loader.reload(plugin_name)
                    log.info("Cascade reloaded: %s", plugin_name)
                except Exception as e:
                    log.error("Cascade reload failed for %s: %s", plugin_name, e)
                    raise
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _rebuild_dependency_graph(self) -> None:
        self._dependency_graph.clear()
        for manifest in self._loader.list_discovered():
            for dep in manifest.dependencies:
                self._dependency_graph[dep].add(manifest.name)

    def _get_dependents(self, name: str) -> set[str]:
        return self._dependency_graph.get(name, set())

    def _check_version_compatibility(self, name: str) -> list[str]:
        manifest = self._loader.get_manifest(name)
        if manifest is None:
            return [f"Plugin '{name}' not found"]
        return check_plugin_compatibility(
            manifest.name,
            manifest.version,
            manifest.version_requirements,
            self._all_versions(),
        )

    def _all_versions(self) -> dict[str, str]:
        return {m.name: m.version for m in self._loader.list_discovered()}
