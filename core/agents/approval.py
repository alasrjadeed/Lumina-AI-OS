"""Approval System — human-in-the-loop permission gates for sensitive agent actions."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from enum import StrEnum

PENDING_DIR = os.path.expanduser("~/.lumina/pending_approvals")


class ApprovalLevel(StrEnum):
    AUTO = "auto"
    NOTIFY = "notify"
    CONFIRM = "confirm"
    REQUIRE = "require"


ACTION_LEVELS: dict[str, ApprovalLevel] = {
    "read_email": ApprovalLevel.AUTO,
    "read_files": ApprovalLevel.AUTO,
    "read_crm": ApprovalLevel.AUTO,
    "generate_report": ApprovalLevel.AUTO,
    "write_code": ApprovalLevel.AUTO,
    "run_tests": ApprovalLevel.AUTO,
    "search_web": ApprovalLevel.AUTO,
    "scrape_data": ApprovalLevel.AUTO,
    "send_email": ApprovalLevel.CONFIRM,
    "send_sms": ApprovalLevel.CONFIRM,
    "send_whatsapp": ApprovalLevel.CONFIRM,
    "draft_email": ApprovalLevel.NOTIFY,
    "create_invoice": ApprovalLevel.CONFIRM,
    "send_invoice": ApprovalLevel.REQUIRE,
    "make_payment": ApprovalLevel.REQUIRE,
    "deploy_code": ApprovalLevel.CONFIRM,
    "push_to_production": ApprovalLevel.REQUIRE,
    "modify_database": ApprovalLevel.CONFIRM,
    "drop_table": ApprovalLevel.REQUIRE,
    "delete_files": ApprovalLevel.CONFIRM,
    "delete_account": ApprovalLevel.REQUIRE,
    "change_pricing": ApprovalLevel.CONFIRM,
    "sign_contract": ApprovalLevel.REQUIRE,
    "access_secrets": ApprovalLevel.REQUIRE,
    "install_software": ApprovalLevel.CONFIRM,
    "modify_system": ApprovalLevel.CONFIRM,
    "post_social": ApprovalLevel.CONFIRM,
    "send_newsletter": ApprovalLevel.CONFIRM,
    "contact_lead": ApprovalLevel.NOTIFY,
    "schedule_meeting": ApprovalLevel.NOTIFY,
    "create_proposal": ApprovalLevel.NOTIFY,
    "send_proposal": ApprovalLevel.CONFIRM,
}


@dataclass
class ApprovalRequest:
    id: str
    action: str
    agent: str
    description: str
    details: dict = field(default_factory=dict)
    level: ApprovalLevel = ApprovalLevel.CONFIRM
    created_at: float = 0.0
    status: str = "pending"
    response: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "action": self.action,
            "agent": self.agent,
            "description": self.description,
            "details": self.details,
            "level": self.level.value,
            "created_at": self.created_at,
            "status": self.status,
            "response": self.response,
        }


class ApprovalGate:
    """Manages human-in-the-loop approval for sensitive agent actions."""

    def __init__(self):
        self._pending: dict[str, ApprovalRequest] = {}
        self._history: list[ApprovalRequest] = []
        self._callbacks: dict[str, list] = {}
        self._auto_approve_patterns: list[str] = []
        self._load()

    def _path(self) -> str:
        os.makedirs(PENDING_DIR, exist_ok=True)
        return os.path.join(PENDING_DIR, "approvals.json")

    def _load(self):
        path = self._path()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                for req_data in data.get("pending", []):
                    req = ApprovalRequest(
                        id=req_data["id"],
                        action=req_data["action"],
                        agent=req_data["agent"],
                        description=req_data["description"],
                        details=req_data.get("details", {}),
                        level=ApprovalLevel(req_data.get("level", "confirm")),
                        created_at=req_data.get("created_at", 0),
                        status=req_data.get("status", "pending"),
                    )
                    self._pending[req.id] = req
                for req_data in data.get("history", []):
                    req = ApprovalRequest(
                        id=req_data["id"],
                        action=req_data["action"],
                        agent=req_data["agent"],
                        description=req_data["description"],
                        details=req_data.get("details", {}),
                        level=ApprovalLevel(req_data.get("level", "confirm")),
                        created_at=req_data.get("created_at", 0),
                        status=req_data.get("status", "unknown"),
                        response=req_data.get("response", ""),
                    )
                    self._history.append(req)
            except Exception:
                pass

    def _save(self):
        data = {
            "pending": [r.to_dict() for r in self._pending.values()],
            "history": [r.to_dict() for r in self._history[-100:]],
        }
        with open(self._path(), "w") as f:
            json.dump(data, f, indent=2)

    def get_level(self, action: str) -> ApprovalLevel:
        return ACTION_LEVELS.get(action, ApprovalLevel.CONFIRM)

    def set_level(self, action: str, level: ApprovalLevel):
        ACTION_LEVELS[action] = level

    def add_auto_approve(self, pattern: str):
        self._auto_approve_patterns.append(pattern)

    def remove_auto_approve(self, pattern: str):
        if pattern in self._auto_approve_patterns:
            self._auto_approve_patterns.remove(pattern)

    def should_auto_approve(self, action: str, description: str) -> bool:
        for pattern in self._auto_approve_patterns:
            if pattern in action or pattern in description:
                return True
        return False

    async def request(
        self,
        action: str,
        agent: str,
        description: str,
        details: dict | None = None,
    ) -> ApprovalRequest:
        import uuid

        level = self.get_level(action)

        if level == ApprovalLevel.AUTO or self.should_auto_approve(action, description):
            req = ApprovalRequest(
                id=uuid.uuid4().hex[:12],
                action=action,
                agent=agent,
                description=description,
                details=details or {},
                level=level,
                created_at=time.time(),
                status="approved",
                response="Auto-approved",
            )
            self._history.append(req)
            self._save()
            return req

        if level == ApprovalLevel.NOTIFY:
            req = ApprovalRequest(
                id=uuid.uuid4().hex[:12],
                action=action,
                agent=agent,
                description=description,
                details=details or {},
                level=level,
                created_at=time.time(),
                status="approved",
                response="Auto-approved (notify)",
            )
            self._history.append(req)
            self._save()
            return req

        req = ApprovalRequest(
            id=uuid.uuid4().hex[:12],
            action=action,
            agent=agent,
            description=description,
            details=details or {},
            level=level,
            created_at=time.time(),
            status="pending",
        )
        self._pending[req.id] = req
        self._save()
        return req

    def approve(self, request_id: str, note: str = "") -> ApprovalRequest | None:
        req = self._pending.pop(request_id, None)
        if req:
            req.status = "approved"
            req.response = note or "Approved"
            self._history.append(req)
            self._save()
            return req
        return None

    def deny(self, request_id: str, reason: str = "") -> ApprovalRequest | None:
        req = self._pending.pop(request_id, None)
        if req:
            req.status = "denied"
            req.response = reason or "Denied"
            self._history.append(req)
            self._save()
            return req
        return None

    def get_pending(self) -> list[ApprovalRequest]:
        return sorted(self._pending.values(), key=lambda r: r.created_at, reverse=True)

    def get_history(self, limit: int = 50) -> list[ApprovalRequest]:
        return sorted(self._history, key=lambda r: r.created_at, reverse=True)[:limit]

    def get_levels(self) -> dict[str, str]:
        return {action: level.value for action, level in ACTION_LEVELS.items()}

    def count_pending(self) -> int:
        return len(self._pending)


approval_gate = ApprovalGate()
