from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from core.desktop.plugin_manager import PluginMetadata
from core.log import log
from core.whatsapp.client import WhatsAppClient


@dataclass
class AutoReplyRule:
    keyword: str
    response: str
    match_type: str = "exact"
    enabled: bool = True


@dataclass
class BroadcastCampaign:
    name: str
    message: str
    recipients: list[str] = field(default_factory=list)
    sent: int = 0
    failed: int = 0
    status: str = "draft"


metadata = PluginMetadata(
    name="WhatsApp Automation",
    version="1.0.0",
    description="WhatsApp message automation with auto-reply, templates, and broadcast campaigns",
    author="Lumina",
    hooks=["message_sent", "auto_reply_triggered", "campaign_completed"],
)

client = WhatsAppClient()
_rules: list[AutoReplyRule] = []
_campaigns: list[BroadcastCampaign] = []
_storage_path = "whatsapp_plugin_data.json"


def on_load() -> None:
    global _rules, _campaigns
    _load_data()
    log.info("WhatsApp Automation plugin loaded")


def on_unload() -> None:
    _save_data()


def on_enable() -> None:
    log.info("WhatsApp Automation enabled")


def on_disable() -> None:
    log.info("WhatsApp Automation disabled")


def _load_data() -> None:
    global _rules, _campaigns
    if os.path.exists(_storage_path):
        try:
            with open(_storage_path) as f:
                data = json.load(f)
            _rules = [AutoReplyRule(**r) for r in data.get("rules", [])]
            _campaigns = [BroadcastCampaign(**c) for c in data.get("campaigns", [])]
        except Exception:
            pass


def _save_data() -> None:
    with open(_storage_path, "w") as f:
        json.dump({
            "rules": [{"keyword": r.keyword, "response": r.response,
                       "match_type": r.match_type, "enabled": r.enabled} for r in _rules],
            "campaigns": [{"name": c.name, "message": c.message,
                           "recipients": c.recipients, "sent": c.sent,
                           "failed": c.failed, "status": c.status} for c in _campaigns],
        }, f, indent=2)


async def send_message(to: str, text: str) -> dict:
    result = await client.send_text(to, text)
    return result


async def send_template(to: str, template_name: str, params: list[str] | None = None) -> dict:
    return await client.send_template(to, template_name, params)


def add_auto_reply(keyword: str, response: str, match_type: str = "exact") -> AutoReplyRule:
    rule = AutoReplyRule(keyword=keyword, response=response, match_type=match_type)
    _rules.append(rule)
    _save_data()
    return rule


def remove_auto_reply(keyword: str) -> bool:
    global _rules
    before = len(_rules)
    _rules = [r for r in _rules if r.keyword != keyword]
    if len(_rules) < before:
        _save_data()
        return True
    return False


def list_auto_replies() -> list[AutoReplyRule]:
    return list(_rules)


def get_matched_reply(incoming_text: str) -> str | None:
    for rule in _rules:
        if not rule.enabled:
            continue
        if rule.match_type == "exact" and incoming_text.lower() == rule.keyword.lower():
            return rule.response
        if rule.match_type == "contains" and rule.keyword.lower() in incoming_text.lower():
            return rule.response
        if (
            rule.match_type == "startswith"
            and incoming_text.lower().startswith(rule.keyword.lower())
        ):
            return rule.response
    return None


def create_campaign(name: str, message: str, recipients: list[str]) -> BroadcastCampaign:
    campaign = BroadcastCampaign(name=name, message=message, recipients=recipients)
    _campaigns.append(campaign)
    _save_data()
    return campaign


async def run_campaign(campaign_name: str) -> dict:
    for c in _campaigns:
        if c.name == campaign_name and c.status == "draft":
            c.status = "running"
            for recipient in c.recipients:
                try:
                    await client.send_text(recipient, c.message)
                    c.sent += 1
                except Exception:
                    c.failed += 1
            c.status = "completed"
            _save_data()
            return {"name": c.name, "sent": c.sent, "failed": c.failed, "status": c.status}
    return {"error": "Campaign not found or already completed"}


def list_campaigns() -> list[BroadcastCampaign]:
    return list(_campaigns)
