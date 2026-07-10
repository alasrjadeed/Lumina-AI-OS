import json

import pytest

from kernel.exceptions import PluginDependencyError, PluginLoadError
from kernel.models import PluginType
from kernel.plugins.registry import PluginRegistry


@pytest.fixture
def registry(tmp_path):
    return PluginRegistry(plugin_dirs=[str(tmp_path)])


def make_plugin(
    tmp_path, name, version="0.1.0", deps=None, reqs=None, entry_point="main", plugin_type=None
):
    d = tmp_path / name
    d.mkdir()
    (d / "__init__.py").write_text("main = None\n")
    manifest = {"name": name, "version": version}
    if deps:
        manifest["dependencies"] = deps
    if reqs:
        manifest["version_requirements"] = reqs
    if plugin_type:
        manifest["plugin_type"] = plugin_type
    if entry_point != "main":
        manifest["entry_point"] = entry_point
    (d / "manifest.json").write_text(json.dumps(manifest))


class TestRegistryDiscovery:
    @pytest.mark.asyncio
    async def test_discover_plugins(self, registry, tmp_path):
        make_plugin(tmp_path, "p1")
        make_plugin(tmp_path, "p2")
        manifests = await registry.discover()
        assert len(manifests) == 2

    @pytest.mark.asyncio
    async def test_discover_adds_plugin_type(self, registry, tmp_path):
        make_plugin(tmp_path, "sys_plugin", plugin_type="system")
        await registry.discover()
        types = registry.find_by_type(PluginType.SYSTEM)
        assert len(types) == 1
        assert types[0].name == "sys_plugin"


class TestRegistryLoad:
    @pytest.mark.asyncio
    async def test_load_simple(self, registry, tmp_path):
        make_plugin(tmp_path, "simple")
        await registry.discover()
        result = await registry.load("simple")
        assert result is None

    @pytest.mark.asyncio
    async def test_load_with_dependency(self, registry, tmp_path):
        make_plugin(tmp_path, "dep_a")
        make_plugin(tmp_path, "main_a", deps=["dep_a"])
        await registry.discover()
        await registry.load("main_a")
        assert "dep_a" in registry.list_loaded()
        assert "main_a" in registry.list_loaded()

    @pytest.mark.asyncio
    async def test_load_checks_version_compatibility(self, registry, tmp_path):
        make_plugin(tmp_path, "dep_b", version="1.0.0")
        make_plugin(tmp_path, "main_b", version="2.0.0", deps=["dep_b"], reqs={"dep_b": ">=2.0.0"})
        await registry.discover()
        with pytest.raises(PluginDependencyError):
            await registry.load("main_b")

    @pytest.mark.asyncio
    async def test_load_not_discovered(self, registry):
        with pytest.raises(PluginLoadError, match="Not discovered"):
            await registry.load("missing")


class TestRegistryQueries:
    @pytest.mark.asyncio
    async def test_search_by_name(self, registry, tmp_path):
        make_plugin(tmp_path, "my_plugin")
        make_plugin(tmp_path, "other")
        await registry.discover()
        results = registry.search("my_plugin")
        assert len(results) == 1
        assert results[0].name == "my_plugin"

    @pytest.mark.asyncio
    async def test_find_by_author(self, registry, tmp_path):
        d = tmp_path / "alice_plugin"
        d.mkdir()
        (d / "__init__.py").write_text("")
        (d / "manifest.json").write_text(
            json.dumps({"name": "alice_plugin", "author": "Alice"}),
        )
        await registry.discover()
        results = registry.find_by_author("Alice")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_version(self, registry, tmp_path):
        make_plugin(tmp_path, "ver_plugin", version="2.3.4")
        await registry.discover()
        v = registry.get_version("ver_plugin")
        assert v is not None
        assert v.major == 2

    @pytest.mark.asyncio
    async def test_get_version_nonexistent(self, registry):
        assert registry.get_version("missing") is None


class TestRegistryDeps:
    @pytest.mark.asyncio
    async def test_get_dependencies(self, registry, tmp_path):
        make_plugin(tmp_path, "dep_x", deps=["a", "b"])
        await registry.discover()
        assert registry.get_dependencies("dep_x") == ["a", "b"]

    @pytest.mark.asyncio
    async def test_get_dependents(self, registry, tmp_path):
        make_plugin(tmp_path, "base")
        make_plugin(tmp_path, "child", deps=["base"])
        await registry.discover()
        deps = registry.get_dependents("base")
        assert "child" in deps

    @pytest.mark.asyncio
    async def test_load_order(self, registry, tmp_path):
        make_plugin(tmp_path, "leaf")
        make_plugin(tmp_path, "middle", deps=["leaf"])
        make_plugin(tmp_path, "root", deps=["middle"])
        await registry.discover()
        order = registry.load_order()
        assert order.index("leaf") < order.index("middle")
        assert order.index("middle") < order.index("root")


class TestRegistryReload:
    @pytest.mark.asyncio
    async def test_reload_simple(self, registry, tmp_path):
        make_plugin(tmp_path, "reload_test")
        await registry.discover()
        await registry.load("reload_test")
        await registry.reload("reload_test")
        assert "reload_test" in registry.list_loaded()

    @pytest.mark.asyncio
    async def test_reload_not_loaded_raises(self, registry, tmp_path):
        make_plugin(tmp_path, "not_loaded")
        await registry.discover()
        with pytest.raises(PluginLoadError):
            await registry.reload("not_loaded")


class TestRegistryUnload:
    @pytest.mark.asyncio
    async def test_unload_with_dependents_raises(self, registry, tmp_path):
        make_plugin(tmp_path, "base_unload")
        make_plugin(tmp_path, "dependent", deps=["base_unload"])
        await registry.discover()
        await registry.load("dependent")
        with pytest.raises(PluginLoadError, match="still required by"):
            await registry.unload("base_unload")


class TestRegistryIncompat:
    @pytest.mark.asyncio
    async def test_list_incompatible(self, registry, tmp_path):
        make_plugin(tmp_path, "good_dep", version="2.0.0")
        make_plugin(
            tmp_path, "bad_plugin", version="1.0.0", deps=["good_dep"], reqs={"good_dep": ">=3.0.0"}
        )
        await registry.discover()
        bad = registry.list_incompatible_plugins()
        assert "bad_plugin" in bad
