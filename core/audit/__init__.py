"""Audit Trail — comprehensive logging of every agent action with rollback support."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from enum import StrEnum

AUDIT_DIR = os.path.expanduser("~/.lumina/audit")


class AuditAction(StrEnum):
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    SEND = "send"
    DEPLOY = "deploy"
    INSTALL = "install"
    APPROVE = "approve"
    DENY = "deny"


@dataclass
class AuditEntry:
    id: str
    action: AuditAction
    agent: str
    target: str
    description: str
    details: dict = field(default_factory=dict)
    status: str = "completed"
    error: str = ""
    rollback_possible: bool = False
    rollback_info: dict = field(default_factory=dict)
    timestamp: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "action": self.action.value,
            "agent": self.agent,
            "target": self.target,
            "description": self.description,
            "details": self.details,
            "status": self.status,
            "error": self.error,
            "rollback_possible": self.rollback_possible,
            "rollback_info": self.rollback_info,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> AuditEntry:
        return cls(
            id=d["id"],
            action=AuditAction(d.get("action", "execute")),
            agent=d.get("agent", ""),
            target=d.get("target", ""),
            description=d.get("description", ""),
            details=d.get("details", {}),
            status=d.get("status", "completed"),
            error=d.get("error", ""),
            rollback_possible=d.get("rollback_possible", False),
            rollback_info=d.get("rollback_info", {}),
            timestamp=d.get("timestamp", 0),
        )


class AuditTrail:
    """Logs every agent action for accountability, debugging, and rollback."""

    def __init__(self):
        self._entries: list[AuditEntry] = []
        self._daily_rotation: dict[str, list[str]] = {}
        self._load()

    def _path(self) -> str:
        os.makedirs(AUDIT_DIR, exist_ok=True)
        return os.path.join(AUDIT_DIR, "trail.json")

    def _today_path(self) -> str:
        os.makedirs(AUDIT_DIR, exist_ok=True)
        return os.path.join(AUDIT_DIR, f"trail_{time.strftime('%Y%m%d')}.json")

    def _load(self):
        path = self._path()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                self._entries = [AuditEntry.from_dict(d) for d in data[-2000:]]
            except Exception:
                pass

    def _save(self):
        with open(self._path(), "w") as f:
            json.dump([e.to_dict() for e in self._entries[-2000:]], f, indent=2)

    def log(
        self,
        action: AuditAction,
        agent: str,
        target: str,
        description: str,
        details: dict | None = None,
        rollback_possible: bool = False,
        rollback_info: dict | None = None,
    ) -> AuditEntry:
        import uuid

        entry = AuditEntry(
            id=uuid.uuid4().hex[:12],
            action=action,
            agent=agent,
            target=target,
            description=description,
            details=details or {},
            status="completed",
            rollback_possible=rollback_possible,
            rollback_info=rollback_info or {},
            timestamp=time.time(),
        )
        self._entries.append(entry)
        self._save()

        today = time.strftime("%Y-%m-%d")
        if today not in self._daily_rotation:
            self._daily_rotation[today] = []
        self._daily_rotation[today].append(entry.id)

        day_entries = self._query_by_date(today)
        if len(day_entries) % 50 == 0:
            with open(self._today_path(), "w") as f:
                json.dump([e.to_dict() for e in day_entries], f, indent=2)

        return entry

    def log_error(
        self,
        agent: str,
        target: str,
        error: str,
        description: str = "",
        details: dict | None = None,
    ) -> AuditEntry:
        import uuid

        entry = AuditEntry(
            id=uuid.uuid4().hex[:12],
            action=AuditAction.EXECUTE,
            agent=agent,
            target=target,
            description=description or f"Error: {error[:100]}",
            details=details or {},
            status="failed",
            error=error,
            timestamp=time.time(),
        )
        self._entries.append(entry)
        self._save()
        return entry

    def _query_by_date(self, date_str: str) -> list[AuditEntry]:
        return [
            e
            for e in self._entries
            if time.strftime("%Y-%m-%d", time.localtime(e.timestamp)) == date_str
        ]

    def query(
        self,
        agent: str = "",
        action: str = "",
        status: str = "",
        since: float = 0,
        limit: int = 100,
    ) -> list[AuditEntry]:
        results = list(self._entries)
        if agent:
            results = [e for e in results if e.agent == agent]
        if action:
            results = [e for e in results if e.action.value == action]
        if status:
            results = [e for e in results if e.status == status]
        if since:
            results = [e for e in results if e.timestamp >= since]
        return sorted(results, key=lambda e: e.timestamp, reverse=True)[:limit]

    def get_today_summary(self) -> dict:
        today = time.strftime("%Y-%m-%d")
        day_entries = self._query_by_date(today)

        by_agent: dict[str, int] = {}
        by_action: dict[str, int] = {}
        errors: list[dict] = []

        for e in day_entries:
            by_agent[e.agent] = by_agent.get(e.agent, 0) + 1
            by_action[e.action.value] = by_action.get(e.action.value, 0) + 1
            if e.status == "failed":
                errors.append({"agent": e.agent, "target": e.target[:100], "error": e.error[:200]})

        return {
            "date": today,
            "total_actions": len(day_entries),
            "by_agent": by_agent,
            "by_action": by_action,
            "errors": len(errors),
            "error_details": errors[:10],
        }

    def get_daily_report(self, date_str: str = "") -> str:
        if not date_str:
            date_str = time.strftime("%Y-%m-%d")
        day_entries = self._query_by_date(date_str)

        if not day_entries:
            return f"No actions recorded on {date_str}."

        reads = sum(1 for e in day_entries if e.action == AuditAction.READ)
        creates = sum(1 for e in day_entries if e.action == AuditAction.CREATE)
        updates = sum(1 for e in day_entries if e.action == AuditAction.UPDATE)
        deletes = sum(1 for e in day_entries if e.action == AuditAction.DELETE)
        sends = sum(1 for e in day_entries if e.action == AuditAction.SEND)
        deploys = sum(1 for e in day_entries if e.action == AuditAction.DEPLOY)
        errors = sum(1 for e in day_entries if e.status == "failed")

        lines = [
            f"# Audit Report — {date_str}",
            "",
            f"**Total actions:** {len(day_entries)}",
            "",
            "| Action | Count |",
            "|--------|-------|",
            f"| Reads | {reads} |",
            f"| Creates | {creates} |",
            f"| Updates | {updates} |",
            f"| Deletes | {deletes} |",
            f"| Sends | {sends} |",
            f"| Deploys | {deploys} |",
            f"| **Errors** | **{errors}** |",
            "",
        ]

        if errors > 0:
            lines.append("## Errors")
            lines.extend(
                f"- [{e.agent}] {e.target[:80]}: {e.error[:120]}"
                for e in day_entries
                if e.status == "failed"
            )
            lines.append("")

        agents = set(e.agent for e in day_entries)
        if agents:
            lines.append("## Active Agents")
            for agent_name in sorted(agents):
                count = sum(1 for e in day_entries if e.agent == agent_name)
                agent_errors = sum(
                    1 for e in day_entries if e.agent == agent_name and e.status == "failed"
                )
                lines.append(
                    f"- {agent_name}: {count} action(s)"
                    + (f", {agent_errors} error(s)" if agent_errors else "")
                )

        return "\n".join(lines)

    def get_stats(self) -> dict:
        return {
            "total_entries": len(self._entries),
            "today": len(self._query_by_date(time.strftime("%Y-%m-%d"))),
            "unique_agents": len({e.agent for e in self._entries}),
            "error_rate": round(
                sum(1 for e in self._entries if e.status == "failed")
                / max(len(self._entries), 1)
                * 100,
                1,
            ),
            "rollback_entries": sum(1 for e in self._entries if e.rollback_possible),
        }

    def clear_old(self, days: int = 90):
        cutoff = time.time() - days * 86400
        self._entries = [e for e in self._entries if e.timestamp >= cutoff]
        self._save()


audit_trail = AuditTrail()
