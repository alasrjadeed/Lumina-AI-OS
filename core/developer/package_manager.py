from __future__ import annotations

import importlib.util
import json
import os
import shutil
import zipfile
from dataclasses import dataclass, field

from core.log import log


@dataclass
class PackageMetadata:
    name: str
    version: str = "0.1.0"
    description: str = ""
    author: str = ""
    dependencies: list[str] = field(default_factory=list)
    min_sdk_version: str = "1.0.0"


@dataclass
class InstalledPackage:
    metadata: PackageMetadata
    path: str = ""
    enabled: bool = True


class PackageManager:
    """Install, uninstall, and manage Lumina packages/plugins."""

    def __init__(self, packages_dir: str = ".lumina_packages"):
        self.packages_dir = packages_dir
        self._installed: dict[str, InstalledPackage] = {}
        os.makedirs(packages_dir, exist_ok=True)
        self._load_index()

    def _index_path(self) -> str:
        return os.path.join(self.packages_dir, "index.json")

    def _load_index(self) -> None:
        path = self._index_path()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                for item in data:
                    meta = PackageMetadata(**item["metadata"])
                    pkg = InstalledPackage(
                        metadata=meta,
                        path=item["path"],
                        enabled=item.get("enabled", True),
                    )
                    self._installed[meta.name] = pkg
            except Exception:
                pass

    def _save_index(self) -> None:
        data = [{
                "metadata": {"name": pkg.metadata.name, "version": pkg.metadata.version,
                             "description": pkg.metadata.description, "author": pkg.metadata.author,
                             "dependencies": pkg.metadata.dependencies,
                             "min_sdk_version": pkg.metadata.min_sdk_version},
                "path": pkg.path,
                "enabled": pkg.enabled,
            } for pkg in self._installed.values()]
        with open(self._index_path(), "w") as f:
            json.dump(data, f, indent=2)

    def install(self, source: str) -> InstalledPackage:
        if source.endswith(".lumina"):
            return self._install_archive(source)
        if os.path.isdir(source):
            return self._install_dir(source)
        raise ValueError(f"Unknown source: {source}")

    def _install_archive(self, path: str) -> InstalledPackage:
        name = os.path.splitext(os.path.basename(path))[0]
        dest = os.path.join(self.packages_dir, name)
        with zipfile.ZipFile(path, "r") as zf:
            zf.extractall(dest)
        metadata = self._read_metadata(dest) or PackageMetadata(name=name)
        pkg = InstalledPackage(metadata=metadata, path=dest)
        self._installed[metadata.name] = pkg
        self._save_index()
        log.info("Package installed from archive: %s v%s", metadata.name, metadata.version)
        return pkg

    def _install_dir(self, path: str) -> InstalledPackage:
        name = os.path.basename(os.path.normpath(path))
        dest = os.path.join(self.packages_dir, name)
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(path, dest)
        metadata = self._read_metadata(dest) or PackageMetadata(name=name)
        pkg = InstalledPackage(metadata=metadata, path=dest)
        self._installed[metadata.name] = pkg
        self._save_index()
        log.info("Package installed from dir: %s v%s", metadata.name, metadata.version)
        return pkg

    def uninstall(self, name: str) -> bool:
        pkg = self._installed.pop(name, None)
        if not pkg:
            return False
        if os.path.exists(pkg.path):
            shutil.rmtree(pkg.path)
        self._save_index()
        log.info("Package uninstalled: %s", name)
        return True

    def list_packages(self) -> list[InstalledPackage]:
        return list(self._installed.values())

    def get_package(self, name: str) -> InstalledPackage | None:
        return self._installed.get(name)

    def is_installed(self, name: str) -> bool:
        return name in self._installed

    def enable(self, name: str) -> bool:
        pkg = self._installed.get(name)
        if pkg:
            pkg.enabled = True
            self._save_index()
            return True
        return False

    def disable(self, name: str) -> bool:
        pkg = self._installed.get(name)
        if pkg:
            pkg.enabled = False
            self._save_index()
            return True
        return False

    def resolve_dependencies(self, name: str) -> list[str]:
        resolved = []
        visited = set()

        def resolve(pkg_name: str, depth: int = 0) -> None:
            if depth > 10 or pkg_name in visited:
                return
            visited.add(pkg_name)
            pkg = self._installed.get(pkg_name)
            if pkg:
                for dep in pkg.metadata.dependencies:
                    resolve(dep, depth + 1)
                    if dep not in resolved:
                        resolved.append(dep)
                if pkg_name not in resolved:
                    resolved.append(pkg_name)

        resolve(name)
        return resolved

    def _read_metadata(self, path: str) -> PackageMetadata | None:
        init_path = os.path.join(path, "__init__.py")
        if os.path.exists(init_path):
            try:
                spec = importlib.util.spec_from_file_location("_pkg_meta", init_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, "metadata"):
                        m = module.metadata
                        return PackageMetadata(
                            name=m.name, version=m.version, description=m.description,
                            author=m.author, dependencies=m.dependencies,
                            min_sdk_version=getattr(m, "min_sdk_version", "1.0.0"),
                        )
            except Exception:
                pass
        meta_path = os.path.join(path, "package.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path) as f:
                    data = json.load(f)
                return PackageMetadata(**data)
            except Exception:
                pass
        return None
