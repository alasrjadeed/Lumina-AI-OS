from __future__ import annotations

import hashlib
import json
import os
import shutil
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from core.log import log


@dataclass
class BackupSnapshot:
    name: str
    path: str
    size: int = 0
    checksum: str = ""
    created: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BackupConfig:
    backup_dir: str = ".lumina_backups"
    max_snapshots: int = 10
    retention_days: float = 30.0
    compress: bool = True
    paths: list[str] = field(default_factory=list)


class Backups:
    """Backup scheduling, snapshot management, restore, and rotation."""

    def __init__(self, config: BackupConfig | None = None):
        self.config = config or BackupConfig()
        self._snapshots: list[BackupSnapshot] = []
        self._hooks: dict[str, list[Callable]] = {}
        os.makedirs(self.config.backup_dir, exist_ok=True)
        self._load_index()

    def _index_path(self) -> str:
        return os.path.join(self.config.backup_dir, "index.json")

    def _load_index(self) -> None:
        path = self._index_path()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                self._snapshots = [BackupSnapshot(**s) for s in data]
            except Exception:
                pass

    def _save_index(self) -> None:
        data = [{"name": s.name, "path": s.path, "size": s.size,
                 "checksum": s.checksum, "created": s.created,
                 "metadata": s.metadata} for s in self._snapshots]
        with open(self._index_path(), "w") as f:
            json.dump(data, f, indent=2)

    def create_snapshot(self, name: str = "", paths: list[str] | None = None,
                        metadata: dict[str, Any] | None = None) -> BackupSnapshot:
        snapshot_name = name or f"backup_{int(time.time())}"
        snapshot_dir = os.path.join(self.config.backup_dir, snapshot_name)
        os.makedirs(snapshot_dir, exist_ok=True)
        backup_paths = paths or self.config.paths
        total_size = 0
        for src in backup_paths:
            if os.path.exists(src):
                dest = os.path.join(snapshot_dir, os.path.basename(src))
                if os.path.isdir(src):
                    shutil.copytree(src, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dest)
                total_size += self._dir_size(dest) if os.path.isdir(dest) else os.path.getsize(dest)
        checksum = self._compute_checksum(snapshot_dir) if backup_paths else ""
        snapshot = BackupSnapshot(
            name=snapshot_name, path=snapshot_dir,
            size=total_size, checksum=checksum,
            metadata=metadata or {},
        )
        self._snapshots.append(snapshot)
        self._rotate()
        self._save_index()
        self._trigger_hook("after_backup", snapshot)
        log.info("Backup created: %s (%d bytes)", snapshot_name, total_size)
        return snapshot

    def list_snapshots(self) -> list[BackupSnapshot]:
        return list(reversed(self._snapshots))

    def get_snapshot(self, name: str) -> BackupSnapshot | None:
        for s in self._snapshots:
            if s.name == name:
                return s
        return None

    def restore(self, name: str, output_dir: str = "") -> str:
        snapshot = self.get_snapshot(name)
        if not snapshot:
            raise ValueError(f"Snapshot not found: {name}")
        restore_dir = output_dir or f"restore_{name}"
        if os.path.exists(snapshot.path):
            if os.path.isdir(snapshot.path):
                shutil.copytree(snapshot.path, restore_dir, dirs_exist_ok=True)
            else:
                shutil.copy2(snapshot.path, restore_dir)
        log.info("Backup restored: %s -> %s", name, restore_dir)
        return restore_dir

    def delete_snapshot(self, name: str) -> bool:
        snapshot = self.get_snapshot(name)
        if not snapshot:
            return False
        if os.path.exists(snapshot.path):
            shutil.rmtree(snapshot.path)
        self._snapshots = [s for s in self._snapshots if s.name != name]
        self._save_index()
        log.info("Backup deleted: %s", name)
        return True

    def verify_snapshot(self, name: str) -> bool:
        snapshot = self.get_snapshot(name)
        if not snapshot or not os.path.exists(snapshot.path):
            return False
        current_checksum = self._compute_checksum(snapshot.path)
        return current_checksum == snapshot.checksum

    def schedule(self, interval_hours: int = 24, paths: list[str] | None = None) -> None:
        def run_scheduled():
            while True:
                time.sleep(interval_hours * 3600)
                try:
                    self.create_snapshot(paths=paths)
                except Exception as e:
                    log.error("Scheduled backup failed: %s", e)
        thread = threading.Thread(target=run_scheduled, daemon=True)
        thread.start()
        log.info("Backup scheduled every %d hours", interval_hours)

    def on(self, event: str, callback: Callable) -> None:
        self._hooks.setdefault(event, []).append(callback)

    def _trigger_hook(self, event: str, *args: Any) -> None:
        for cb in self._hooks.get(event, []):
            try:
                cb(*args)
            except Exception as e:
                log.error("Backup hook '%s' failed: %s", event, e)

    def _rotate(self) -> None:
        before = len(self._snapshots)
        now = time.time()
        self._snapshots = [
            s for s in self._snapshots
            if (now - s.created) <= self.config.retention_days * 86400
        ]
        while len(self._snapshots) > self.config.max_snapshots:
            oldest = min(self._snapshots, key=lambda s: s.created)
            self._snapshots.remove(oldest)
            if os.path.exists(oldest.path):
                shutil.rmtree(oldest.path)
        if len(self._snapshots) < before:
            self._save_index()

    def _compute_checksum(self, path: str) -> str:
        h = hashlib.sha256()
        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                for f in sorted(files):
                    filepath = os.path.join(root, f)
                    with open(filepath, "rb") as fh:
                        for chunk in iter(lambda: fh.read(8192), b""):
                            h.update(chunk)
        else:
            with open(path, "rb") as fh:
                for chunk in iter(lambda: fh.read(8192), b""):
                    h.update(chunk)
        return h.hexdigest()

    def _dir_size(self, path: str) -> int:
        total = 0
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total += os.path.getsize(fp)
        return total

    @staticmethod
    def default_config() -> BackupConfig:
        return BackupConfig(
            backup_dir=".lumina_backups",
            max_snapshots=10,
            retention_days=30,
            paths=["lumina_memory.json", "lumina_auth.json", "lumina_settings.json"],
        )
