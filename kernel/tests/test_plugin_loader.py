import pytest
from pathlib import Path
import json
import tempfile
from kernel.plugins.plugin_loader import PluginLoader, PluginManifest


@pytest.fixture
def plugin_dir(tmp_path):
    plugin_path = tmp_path / "test_plugin"
    plugin_path.mkdir()
    manifest = {
        "name": "test_plugin",
        "version": "1.0.0",
        "description": "Test plugin",
        "author": "Lumina",
        "entry_point": "main",
    }
    (plugin_path / "manifest.json").write_text(json.dumps(manifest))
    (plugin_path / "main.py").write_text(
        "class TestPlugin:\n    __plugin__ = True\n    def on_load(self): pass\n"
    )
    return tmp_path


def test_discover(plugin_dir):
    loader = PluginLoader(plugin_dir)
    discovered = loader.discover()
    assert len(discovered) == 1
    assert discovered[0].manifest.name == "test_plugin"


def test_load_plugin(plugin_dir):
    loader = PluginLoader(plugin_dir)
    loader.discover()
    info = loader.load("test_plugin")
    assert info is not None
    assert info.is_loaded is True
    assert info.instance is not None


def test_unload_plugin(plugin_dir):
    loader = PluginLoader(plugin_dir)
    loader.discover()
    loader.load("test_plugin")
    assert loader.unload("test_plugin") is True
    assert loader.get_plugin("test_plugin").is_loaded is False


def test_reload_plugin(plugin_dir):
    loader = PluginLoader(plugin_dir)
    loader.discover()
    info = loader.reload("test_plugin")
    assert info is not None
    assert info.is_loaded is True


def test_loaded_plugins(plugin_dir):
    loader = PluginLoader(plugin_dir)
    loader.discover()
    assert len(loader.loaded_plugins()) == 0
    loader.load("test_plugin")
    assert len(loader.loaded_plugins()) == 1


def test_get_instance(plugin_dir):
    loader = PluginLoader(plugin_dir)
    loader.discover()
    loader.load("test_plugin")
    instance = loader.get_instance("test_plugin")
    assert instance is not None
