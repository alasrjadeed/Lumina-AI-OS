"""Lumina AI OS — Plugin Development Example.

This demonstrates creating and loading a custom plugin
using the Plugin SDK and PluginManager.

Run: python examples/plugin_example.py
"""

import os
import tempfile

from core.desktop.plugin_manager import PluginManager
from core.developer.sdk import PluginSDK


def demo_scaffold_plugin():
    """Use the Plugin SDK to scaffold a new plugin."""
    sdk = PluginSDK()
    with tempfile.TemporaryDirectory() as tmpdir:
        files = sdk.scaffold(
            name="hello_plugin",
            description="A simple greeting plugin",
            author="Developer",
            version="1.0.0",
            output_dir=tmpdir,
        )
        print(f"Scaffolded {len(files)} files:")
        for f in files:
            print(f"  - {f}")

        # Validate the plugin
        plugin_dir = os.path.join(tmpdir, "plugins", "hello_plugin")
        issues = sdk.validate(plugin_dir)
        if issues:
            print(f"Validation issues: {issues}")
        else:
            print("Plugin validation: PASSED")

        # Load the plugin via PluginManager
        pm = PluginManager(plugin_dirs=[os.path.join(tmpdir, "plugins")])
        ok = pm.load("hello_plugin")
        print(f"Plugin loaded: {ok}")
        if ok:
            info = pm.get_plugin("hello_plugin")
            print(f"  Name: {info.metadata.name}")
            print(f"  Version: {info.metadata.version}")
            print(f"  Author: {info.metadata.author}")
            pm.unload("hello_plugin")
            print("Plugin unloaded.")


def demo_list_builtin_plugins():
    """List all built-in plugins using PluginManager."""
    pm = PluginManager()
    count = pm.load_all()
    print(f"\nLoaded {count} built-in plugins:")
    for info in pm.list_plugins():
        print(f"  - {info.metadata.name} v{info.metadata.version}")
        if info.metadata.hooks:
            print(f"    hooks: {info.metadata.hooks}")
    pm.unload_all()


if __name__ == "__main__":
    print("=" * 60)
    print("Lumina Plugin Development Example")
    print("=" * 60)

    print("\n1. Scaffolding a Plugin")
    print("-" * 40)
    demo_scaffold_plugin()

    print("\n2. Built-in Plugins")
    print("-" * 40)
    demo_list_builtin_plugins()

    print("\n" + "=" * 60)
    print("Done.")
    print("=" * 60)
