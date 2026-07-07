from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

from core.desktop.plugin_manager import PluginMetadata
from core.log import log

LEAD_SOURCES = ["website", "referral", "social_media", "email", "phone", "chat", "event", "other"]
LEAD_STATUSES = ["new", "contacted", "qualified", "proposal", "negotiation", "won", "lost"]


@dataclass
class Lead:
    id: str = ""
    name: str = ""
    email: str = ""
    phone: str = ""
    source: str = "website"
    status: str = "new"
    score: int = 0
    company: str = ""
    notes: str = ""
    created: float = field(default_factory=time.time)
    last_contacted: float = 0.0


@dataclass
class LeadScoreRule:
    field: str
    operator: str
    value: str
    points: int = 10


metadata = PluginMetadata(
    name="Lead Management",
    version="1.0.0",
    description="Lead capture, scoring, tracking, and source attribution",
    author="Lumina",
    hooks=["lead_created", "lead_converted", "lead_scored"],
)

_leads: dict[str, Lead] = {}
_score_rules: list[LeadScoreRule] = []
_storage_path = "leads_plugin_data.json"


def on_load() -> None:
    _load_data()
    log.info("Lead Management plugin loaded")


def on_unload() -> None:
    _save_data()


def on_enable() -> None:
    log.info("Lead Management enabled")


def on_disable() -> None:
    log.info("Lead Management disabled")


def _load_data() -> None:
    global _leads, _score_rules
    if os.path.exists(_storage_path):
        try:
            with open(_storage_path) as f:
                data = json.load(f)
            _leads = {k: Lead(**v) for k, v in data.get("leads", {}).items()}
            _score_rules = [LeadScoreRule(**r) for r in data.get("score_rules", [])]
        except Exception:
            pass


def _save_data() -> None:
    with open(_storage_path, "w") as f:
        json.dump({
            "leads": {
                lid: {
                    "id": lead.id, "name": lead.name, "email": lead.email,
                    "phone": lead.phone, "source": lead.source,
                    "status": lead.status, "score": lead.score,
                    "company": lead.company, "notes": lead.notes,
                    "created": lead.created,
                    "last_contacted": lead.last_contacted,
                }
                for lid, lead in _leads.items()
            },
            "score_rules": [{"field": r.field, "operator": r.operator,
                             "value": r.value, "points": r.points} for r in _score_rules],
        }, f, indent=2)


def _next_id() -> str:
    return f"lead_{int(time.time())}_{len(_leads)}"


def add_lead(name: str, email: str = "", phone: str = "", source: str = "website",
             company: str = "", notes: str = "") -> Lead:
    lead = Lead(id=_next_id(), name=name, email=email, phone=phone,
                source=source, company=company, notes=notes)
    lead.score = _calculate_score(lead)
    _leads[lead.id] = lead
    _save_data()
    log.info("Lead created: %s (source: %s)", name, source)
    return lead


def get_lead(lead_id: str) -> Lead | None:
    return _leads.get(lead_id)


def update_lead(lead_id: str, **updates: Any) -> Lead | None:
    lead = _leads.get(lead_id)
    if not lead:
        return None
    for key, value in updates.items():
        if hasattr(lead, key):
            setattr(lead, key, value)
    lead.score = _calculate_score(lead)
    _save_data()
    return lead


def update_status(lead_id: str, status: str) -> bool:
    if status not in LEAD_STATUSES:
        return False
    lead = _leads.get(lead_id)
    if not lead:
        return False
    lead.status = status
    if status in ("contacted", "qualified"):
        lead.last_contacted = time.time()
    _save_data()
    return True


def list_leads(status: str = "", source: str = "", limit: int = 100) -> list[Lead]:
    results = list(_leads.values())
    if status:
        results = [lead for lead in results if lead.status == status]
    if source:
        results = [lead for lead in results if lead.source == source]
    results.sort(key=lambda lead: lead.score, reverse=True)
    return results[:limit]


def search_leads(query: str) -> list[Lead]:
    q = query.lower()
    return [lead for lead in _leads.values()
            if q in lead.name.lower() or q in lead.email.lower() or q in lead.company.lower()]


def delete_lead(lead_id: str) -> bool:
    if lead_id in _leads:
        del _leads[lead_id]
        _save_data()
        return True
    return False


def add_score_rule(field: str, operator: str, value: str, points: int = 10) -> LeadScoreRule:
    rule = LeadScoreRule(field=field, operator=operator, value=value, points=points)
    _score_rules.append(rule)
    _save_data()
    return rule


def _calculate_score(lead: Lead) -> int:
    score = 0
    for rule in _score_rules:
        val = getattr(lead, rule.field, "")
        if (
            rule.operator == "equals" and str(val) == rule.value
            or rule.operator == "contains" and rule.value.lower() in str(val).lower()
            or rule.operator == "not_empty" and str(val).strip()
        ):
            score += rule.points
    return score


def get_analytics() -> dict:
    total = len(_leads)
    by_source = {}
    by_status = {}
    for lead in _leads.values():
        by_source[lead.source] = by_source.get(lead.source, 0) + 1
        by_status[lead.status] = by_status.get(lead.status, 0) + 1
    return {
        "total_leads": total,
        "by_source": by_source,
        "by_status": by_status,
        "avg_score": sum(lead.score for lead in _leads.values()) / total if total else 0,
        "conversion_rate": (by_status.get("won", 0) / total * 100) if total else 0,
    }
