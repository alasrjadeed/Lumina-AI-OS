from __future__ import annotations

import importlib.util
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from typing import Any

try:
    import httpx as _httpx
except ImportError:
    _httpx = None

from core.developer.templates import TemplateManager
from core.log import log


@dataclass
class PluginScaffold:
    name: str
    description: str = ""
    author: str = ""
    version: str = "0.1.0"
    path: str = ""
    hooks: list[str] = field(default_factory=list)


class PluginSDK:
    """Software development kit for building and testing plugins."""

    def __init__(self):
        self.templates = TemplateManager()

    def scaffold(self, name: str, description: str = "", author: str = "",
                 version: str = "0.1.0", output_dir: str = ".") -> list[str]:
        files = self.templates.render("plugin", {
            "name": name,
            "description": description or f"{name} plugin",
            "author": author or "unknown",
            "version": version,
        }, output_dir=output_dir)
        log.info("Plugin scaffolded: %s (%d files)", name, len(files))
        return files

    def validate(self, plugin_path: str) -> list[str]:
        issues = []
        if not os.path.exists(plugin_path):
            return ["Path does not exist"]
        init_path = (
            os.path.join(plugin_path, "__init__.py")
            if os.path.isdir(plugin_path)
            else plugin_path
        )
        if not os.path.exists(init_path):
            return ["No __init__.py found"]
        try:
            spec = importlib.util.spec_from_file_location("_plugin_check", init_path)
            if not spec or not spec.loader:
                return ["Failed to load plugin module"]
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if not hasattr(module, "metadata"):
                issues.append("Missing 'metadata' attribute")
            if not hasattr(module, "on_load"):
                issues.append("Missing 'on_load' function")
            if not hasattr(module, "on_unload"):
                issues.append("Missing 'on_unload' function")
        except Exception as e:
            issues.append(f"Load error: {e}")
        return issues

    def build(self, plugin_path: str, output_path: str = "") -> str:
        issues = self.validate(plugin_path)
        if issues:
            raise ValueError(f"Plugin validation failed: {'; '.join(issues)}")
        name = os.path.basename(plugin_path.rstrip("/"))
        out = output_path or f"{name}.lumina"
        with tempfile.TemporaryDirectory() as tmp:
            base = os.path.join(tmp, name)
            if os.path.isdir(plugin_path):
                shutil.copytree(plugin_path, base)
            else:
                os.makedirs(base)
                shutil.copy2(plugin_path, base)
            shutil.make_archive(out.replace(".lumina", ""), "zip", tmp)
            if not out.endswith(".lumina"):
                out += ".lumina"
            os.rename(out.replace(".lumina", "") + ".zip", out)
        log.info("Plugin built: %s", out)
        return out

    def get_hooks(self, plugin_path: str) -> list[str]:
        hooks = []
        init_path = (
            os.path.join(plugin_path, "__init__.py")
            if os.path.isdir(plugin_path)
            else plugin_path
        )
        try:
            spec = importlib.util.spec_from_file_location("_hook_check", init_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, "metadata") and hasattr(module.metadata, "hooks"):
                    hooks = module.metadata.hooks
        except Exception:
            pass
        return hooks

    def create_api_client(self, base_url: str = "http://localhost:8741") -> SDKAPIClient:
        return SDKAPIClient(base_url)


class SDKAPIClient:
    """API client for interacting with the Lumina platform."""

    def __init__(self, base_url: str = "http://localhost:8741"):
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, endpoint: str, data: Any = None) -> dict:
        if _httpx is None:
            return {"error": "httpx not installed"}
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            with _httpx.Client(timeout=30) as client:
                resp = client.request(method, url, json=data)
                return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def ping(self) -> dict:
        return self._request("GET", "ping")

    def execute_command(self, command: dict) -> dict:
        return self._request("POST", "execute", command)
