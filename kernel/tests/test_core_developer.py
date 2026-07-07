from __future__ import annotations

import os
from pathlib import Path

import pytest

from core.developer.cli import CLI, CLICommand, cli
from core.developer.docs import DocModule, DocumentationGenerator
from core.developer.package_manager import InstalledPackage, PackageManager, PackageMetadata
from core.developer.sdk import PluginSDK
from core.developer.templates import Template, TemplateFile, TemplateManager


class TestCLI:
    def test_default_instance(self):
        assert cli.name == "lumina"

    def test_register_and_list(self):
        c = CLI("test")
        cmd = CLICommand(name="greet", help="Says hello", handler=lambda: "hello")
        c.register(cmd)
        assert c.get_command("greet") is cmd
        assert len(c.list_commands()) >= 1

    def test_decorator(self):
        c = CLI("test")

        @c.command("ping", "Ping pong")
        def ping():
            return "pong"

        assert c.get_command("ping") is not None

    def test_run_unknown(self):
        c = CLI("test")
        code = c.run(["unknown"])
        assert code == 1

    def test_run_no_command(self):
        c = CLI("test")
        code = c.run([])
        assert code == 1

    def test_run_success(self):
        c = CLI("test")

        @c.command("echo", "Echo", args=[{"flags": ["--text"], "default": ""}])
        def echo(text: str = ""):
            return text

        code = c.run(["echo", "--text", "hello"])
        assert code == 0

    def test_format_table(self):
        c = CLI("test")
        table = c.format_table(["Name", "Age"], [["Alice", "30"], ["Bob", "25"]])
        assert "Alice" in table
        assert "Bob" in table

    def test_color(self):
        assert "\033[32m" in CLI.success("ok")
        assert "\033[31m" in CLI.error("fail")


class TestTemplates:
    def test_list_builtins(self):
        tm = TemplateManager()
        names = [t.name for t in tm.list_templates()]
        assert "plugin" in names
        assert "module" in names

    def test_get_template(self):
        tm = TemplateManager()
        t = tm.get("plugin")
        assert t is not None
        assert len(t.files) > 0

    def test_register_custom(self):
        tm = TemplateManager()
        tm.register(Template(name="custom", files=[TemplateFile(path="test.txt", content="hello")]))
        assert tm.get("custom") is not None

    def test_render_plugin(self, tmp_path: Path):
        tm = TemplateManager()
        files = tm.render("plugin", {"name": "myplugin", "description": "Test",
                                      "author": "me", "version": "1.0.0"}, str(tmp_path))
        assert len(files) >= 1
        init_file = [f for f in files if f.endswith("__init__.py")][0]
        content = Path(init_file).read_text()
        assert "myplugin" in content
        assert "Test" in content

    def test_render_nonexistent(self):
        tm = TemplateManager()
        with pytest.raises(ValueError):
            tm.render("nonexistent", {})

    def test_substitute(self):
        tm = TemplateManager()
        result = tm._substitute("Hello {{name}}!", {"name": "World"})
        assert result == "Hello World!"

    def test_create_from_string(self, tmp_path: Path):
        tm = TemplateManager()
        path = tm.create_from_string("test", "{{greeting}} World!", str(tmp_path / "out.txt"),
                                      {"greeting": "Hello"})
        assert Path(path).read_text() == "Hello World!"


class TestPluginSDK:
    def test_init(self):
        sdk = PluginSDK()
        assert sdk.templates is not None

    def test_scaffold(self, tmp_path: Path):
        sdk = PluginSDK()
        files = sdk.scaffold("test_plugin", "A test plugin", "dev", "0.1.0", str(tmp_path))
        assert len(files) >= 1
        init_file = [f for f in files if f.endswith("__init__.py")][0]
        assert os.path.exists(init_file)

    def test_validate_valid(self, tmp_path: Path):
        sdk = PluginSDK()
        sdk.scaffold("valid_plugin", output_dir=str(tmp_path))
        plugin_dir = os.path.join(str(tmp_path), "plugins", "valid_plugin")
        issues = sdk.validate(plugin_dir)
        assert len(issues) == 0

    def test_validate_missing(self):
        sdk = PluginSDK()
        issues = sdk.validate("/nonexistent")
        assert len(issues) >= 1

    def test_invalid_plugin(self, tmp_path: Path):
        sdk = PluginSDK()
        bad_dir = tmp_path / "bad_plugin"
        bad_dir.mkdir()
        (bad_dir / "__init__.py").write_text("# no metadata")
        issues = sdk.validate(str(bad_dir))
        assert len(issues) >= 1

    def test_build(self, tmp_path: Path):
        sdk = PluginSDK()
        sdk.scaffold("build_plugin", output_dir=str(tmp_path))
        plugin_dir = os.path.join(str(tmp_path), "plugins", "build_plugin")
        out = sdk.build(plugin_dir, str(tmp_path / "output.lumina"))
        assert os.path.exists(out)
        assert out.endswith(".lumina")

    def test_get_hooks(self, tmp_path: Path):
        sdk = PluginSDK()
        sdk.scaffold("hooked_plugin", output_dir=str(tmp_path))
        plugin_dir = os.path.join(str(tmp_path), "plugins", "hooked_plugin")
        hooks = sdk.get_hooks(plugin_dir)
        assert isinstance(hooks, list)

    def test_api_client(self):
        sdk = PluginSDK()
        client = sdk.create_api_client("http://localhost:9999")
        assert client.base_url == "http://localhost:9999"


class TestPackageManager:
    def test_init(self, tmp_path: Path):
        pm = PackageManager(packages_dir=str(tmp_path / "pkgs"))
        assert pm.list_packages() == []

    def test_install_dir(self, tmp_path: Path):
        src = tmp_path / "my_package"
        src.mkdir()
        (src / "__init__.py").write_text("""
from core.desktop.plugin_manager import PluginMetadata
metadata = PluginMetadata(name="my_package", version="1.0.0")
def on_load(): pass
def on_unload(): pass
def on_enable(): pass
def on_disable(): pass
""")
        pm = PackageManager(packages_dir=str(tmp_path / "pkgs"))
        pkg = pm.install(str(src))
        assert pkg.metadata.name == "my_package"
        assert pm.is_installed("my_package")

    def test_uninstall(self, tmp_path: Path):
        src = tmp_path / "to_uninstall"
        src.mkdir()
        (src / "__init__.py").write_text("""
from core.desktop.plugin_manager import PluginMetadata
metadata = PluginMetadata(name="to_uninstall")
def on_load(): pass
def on_unload(): pass
""")
        pm = PackageManager(packages_dir=str(tmp_path / "pkgs"))
        pm.install(str(src))
        assert pm.uninstall("to_uninstall")
        assert not pm.uninstall("nonexistent")

    def test_list_packages(self, tmp_path: Path):
        pm = PackageManager(packages_dir=str(tmp_path / "pkgs"))
        assert len(pm.list_packages()) == 0

    def test_enable_disable(self, tmp_path: Path):
        src = tmp_path / "toggle_pkg"
        src.mkdir()
        (src / "__init__.py").write_text("# test")
        pm = PackageManager(packages_dir=str(tmp_path / "pkgs"))
        pm._installed["toggle_pkg"] = InstalledPackage(
            metadata=PackageMetadata(name="toggle_pkg"), path=str(src),
        )
        assert pm.disable("toggle_pkg")
        assert not pm._installed["toggle_pkg"].enabled
        assert pm.enable("toggle_pkg")
        assert pm._installed["toggle_pkg"].enabled

    def test_resolve_dependencies(self, tmp_path: Path):
        pm = PackageManager(packages_dir=str(tmp_path / "pkgs"))
        a = InstalledPackage(metadata=PackageMetadata(name="a", dependencies=["b"]))
        b = InstalledPackage(metadata=PackageMetadata(name="b", dependencies=["c"]))
        c = InstalledPackage(metadata=PackageMetadata(name="c"))
        pm._installed = {"a": a, "b": b, "c": c}
        resolved = pm.resolve_dependencies("a")
        assert "c" in resolved
        assert "b" in resolved

    def test_install_raises_on_unknown(self, tmp_path: Path):
        pm = PackageManager(packages_dir=str(tmp_path / "pkgs"))
        with pytest.raises(ValueError):
            pm.install("unknown.format")


class TestDocumentationGenerator:
    def test_extract_module(self):
        gen = DocumentationGenerator()
        path = os.path.join(os.path.dirname(__file__), "..", "core", "developer", "cli.py")
        if os.path.exists(path):
            doc = gen.extract_module(path)
            assert doc.name == "cli"
            assert len(doc.classes) >= 1

    def test_generate_markdown(self):
        gen = DocumentationGenerator()
        mod = DocModule(name="test", docstring="A test module")
        md = gen.generate_markdown(mod)
        assert "Module: `test`" in md

    def test_generate_api_reference(self):
        gen = DocumentationGenerator()
        md = gen.generate_api_reference([DocModule(name="mod1"), DocModule(name="mod2")])
        assert "mod1" in md
        assert "mod2" in md

    def test_generate_readme(self):
        gen = DocumentationGenerator()
        readme = gen.generate_readme("My Project", "A cool project")
        assert "# My Project" in readme
        assert "A cool project" in readme
        assert "pip install" in readme

    def test_export_markdown(self, tmp_path: Path):
        gen = DocumentationGenerator()
        path = gen.export_markdown(DocModule(name="test"), str(tmp_path / "docs.md"))
        assert Path(path).exists()
        assert "Module: `test`" in Path(path).read_text()

    def test_extract_directory(self):
        gen = DocumentationGenerator()
        dev_dir = os.path.join(os.path.dirname(__file__), "..", "core", "developer")
        if os.path.exists(dev_dir):
            modules = gen.extract_directory(dev_dir)
            assert len(modules) >= 1
