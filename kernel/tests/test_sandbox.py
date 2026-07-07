import json
import sys

import pytest

from kernel.dependency import DIContainer
from kernel.plugins.loader import PluginLoader
from kernel.plugins.sandbox import SandboxedPlugin, SandboxedPluginLoader


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="multiprocessing sandbox not fully supported on Windows",
)
@pytest.mark.asyncio
async def test_sandbox_lifecycle(tmp_path):
    plugin_dir = tmp_path / "sandbox_test"
    plugin_dir.mkdir()
    (plugin_dir / "__init__.py").write_text(
        "class main:\n"
        "    async def on_load(self, container=None):\n"
        "        return 'loaded'\n"
        "    async def on_unload(self):\n"
        "        return 'unloaded'\n"
        "    async def on_enable(self):\n"
        "        return 'enabled'\n"
    )

    sandbox = SandboxedPlugin(name="sandbox_test", plugin_dir=str(plugin_dir))
    await sandbox.start()
    assert sandbox.is_alive

    result = await sandbox.call("on_load")
    assert "loaded" in str(result)

    result = await sandbox.call("on_enable")
    assert "enabled" in str(result)

    result = await sandbox.call("on_unload")
    assert "unloaded" in str(result)

    await sandbox.stop()
    assert not sandbox.is_alive


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="multiprocessing sandbox not fully supported on Windows",
)
@pytest.mark.asyncio
async def test_sandbox_restart(tmp_path):
    plugin_dir = tmp_path / "restart_test"
    plugin_dir.mkdir()
    (plugin_dir / "__init__.py").write_text(
        "class main:\n"
        "    async def ping(self):\n"
        "        return 'pong'\n"
    )

    sandbox = SandboxedPlugin(name="restart_test", plugin_dir=str(plugin_dir))
    await sandbox.start()

    await sandbox.stop()
    assert not sandbox.is_alive

    await sandbox.start()
    assert sandbox.is_alive
    result = await sandbox.call("ping")
    assert result == "pong"
    await sandbox.stop()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="multiprocessing sandbox not fully supported on Windows",
)
@pytest.mark.asyncio
async def test_sandbox_error_raises(tmp_path):
    plugin_dir = tmp_path / "error_test"
    plugin_dir.mkdir()
    (plugin_dir / "__init__.py").write_text(
        "class main:\n"
        "    async def fail(self):\n"
        "        raise ValueError('intentional')\n"
    )

    sandbox = SandboxedPlugin(name="error_test", plugin_dir=str(plugin_dir))
    await sandbox.start()

    with pytest.raises(RuntimeError, match="intentional"):
        await sandbox.call("fail")
    await sandbox.stop()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="multiprocessing sandbox not fully supported on Windows",
)
@pytest.mark.asyncio
async def test_sandbox_not_started_raises():
    sandbox = SandboxedPlugin(name="nope", plugin_dir="/tmp")
    with pytest.raises(RuntimeError, match="not started"):
        await sandbox.call("on_load")


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="multiprocessing sandbox not fully supported on Windows",
)
@pytest.mark.asyncio
async def test_sandbox_stop_idempotent(tmp_path):
    plugin_dir = tmp_path / "idempotent"
    plugin_dir.mkdir()
    (plugin_dir / "__init__.py").write_text("class main:\n    pass\n")

    sandbox = SandboxedPlugin(name="idempotent", plugin_dir=str(plugin_dir))
    await sandbox.stop()
    await sandbox.stop()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="multiprocessing sandbox not fully supported on Windows",
)
@pytest.mark.asyncio
async def test_sandboxed_plugin_loader(tmp_path):

    container = DIContainer()
    loader = PluginLoader(plugin_dirs=[str(tmp_path)], container=container)

    plugin_dir = tmp_path / "sandbox_loader_test"
    plugin_dir.mkdir()
    (plugin_dir / "__init__.py").write_text(
        "class main:\n"
        "    async def on_load(self, container=None):\n"
        "        return 'loaded'\n"
    )
    (plugin_dir / "manifest.json").write_text(
        json.dumps({
            "name": "sandbox_loader_test",
            "version": "1.0.0",
            "entry_point": "main",
        }),
    )

    await loader.discover()
    sandbox_loader = SandboxedPluginLoader(loader)
    sandbox = await sandbox_loader.load("sandbox_loader_test")

    assert sandbox.is_alive
    result = await sandbox.call("on_load")
    assert "loaded" in str(result)

    await sandbox_loader.unload("sandbox_loader_test")
    assert not sandbox.is_alive
