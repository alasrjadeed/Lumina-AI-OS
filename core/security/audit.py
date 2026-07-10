from __future__ import annotations

import csv
import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

from core.log import log


@dataclass
class AuditEvent:
    action: str
    actor: str = ""
    resource: str = ""
    result: str = "success"
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    ip: str = ""
    id: str = ""
    previous_hash: str = ""
    hash: str = ""


class AuditLogger:
    """Tamper-evident audit logging with chain hashing."""

    def __init__(self, storage_path: str = "lumina_audit.json"):
        self.storage_path = storage_path
        self._events: list[AuditEvent] = []
        self._load()

    def log(
        self,
        action: str,
        actor: str = "",
        resource: str = "",
        result: str = "success",
        details: dict[str, Any] | None = None,
        ip: str = "",
    ) -> AuditEvent:
        previous_hash = self._events[-1].hash if self._events else ""
        event = AuditEvent(
            action=action,
            actor=actor,
            resource=resource,
            result=result,
            details=details or {},
            ip=ip,
            id=f"evt_{int(time.time() * 1000)}_{len(self._events)}",
        )
        event.previous_hash = previous_hash
        event.hash = self._compute_hash(event)
        self._events.append(event)
        self._save()
        if result == "failure":
            log.warning("Audit: %s by %s on %s - FAILED", action, actor, resource)
        else:
            log.info("Audit: %s by %s on %s", action, actor, resource)
        return event

    def query(
        self,
        action: str = "",
        actor: str = "",
        resource: str = "",
        result: str = "",
        limit: int = 100,
    ) -> list[AuditEvent]:
        results = list(self._events)
        if action:
            results = [e for e in results if e.action == action]
        if actor:
            results = [e for e in results if actor.lower() in e.actor.lower()]
        if resource:
            results = [e for e in results if resource.lower() in e.resource.lower()]
        if result:
            results = [e for e in results if e.result == result]
        results.reverse()
        return results[:limit]

    def get_recent(self, limit: int = 50) -> list[AuditEvent]:
        return list(reversed(self._events[-limit:]))

    def get_by_user(self, actor: str, limit: int = 50) -> list[AuditEvent]:
        return [e for e in reversed(self._events) if e.actor == actor][:limit]

    def get_failures(self, limit: int = 50) -> list[AuditEvent]:
        return [e for e in reversed(self._events) if e.result == "failure"][:limit]

    def verify_chain(self) -> list[int]:
        return [i for i in range(len(self._events)) if not self.verify_event(i)]

    def verify_event(self, index: int) -> bool:
        if index < 0 or index >= len(self._events):
            return False
        expected = self._compute_hash(self._events[index])
        return self._events[index].hash == expected

    def export(self, path: str = "", format: str = "json") -> str:
        export_path = path or f"audit_export.{format}"
        if format == "json":
            data = [
                {
                    "id": e.id,
                    "action": e.action,
                    "actor": e.actor,
                    "resource": e.resource,
                    "result": e.result,
                    "details": e.details,
                    "timestamp": e.timestamp,
                    "ip": e.ip,
                    "hash": e.hash,
                }
                for e in self._events
            ]
            with open(export_path, "w") as f:
                json.dump(data, f, indent=2)
        elif format == "csv":
            with open(export_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["id", "action", "actor", "resource", "result", "timestamp", "ip", "hash"]
                )
                for e in self._events:
                    writer.writerow(
                        [e.id, e.action, e.actor, e.resource, e.result, e.timestamp, e.ip, e.hash]
                    )
        return export_path

    def count(self) -> int:
        return len(self._events)

    def clear(self) -> None:
        self._events.clear()
        self._save()

    def _compute_hash(self, event: AuditEvent) -> str:
        data = (
            f"{event.id}:{event.action}:{event.actor}:{event.resource}"
            f":{event.result}:{event.timestamp}:{event.previous_hash}"
        )
        return hashlib.sha256(data.encode()).hexdigest()

    def _save(self) -> None:
        data = [
            {
                "id": e.id,
                "action": e.action,
                "actor": e.actor,
                "resource": e.resource,
                "result": e.result,
                "details": e.details,
                "timestamp": e.timestamp,
                "ip": e.ip,
                "previous_hash": e.previous_hash,
                "hash": e.hash,
            }
            for e in self._events
        ]
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load(self) -> None:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path) as f:
                    data = json.load(f)
                for d in data:
                    self._events.append(AuditEvent(**d))
            except Exception:
                pass
