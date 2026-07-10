"""Email automation — SMTP sending, templates, campaigns."""

from __future__ import annotations

import csv
import json
import os
import re
import smtplib
from dataclasses import dataclass, field
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from core.desktop.plugin_manager import PluginMetadata
from core.log import log


@dataclass
class EmailTemplate:
    name: str
    subject: str
    body: str
    is_html: bool = False
    variables: list[str] = field(default_factory=list)


@dataclass
class EmailCampaign:
    name: str
    template: str = ""
    recipients: list[str] = field(default_factory=list)
    sent: int = 0
    failed: int = 0
    opened: int = 0
    status: str = "draft"


metadata = PluginMetadata(
    name="Email Automation",
    version="1.0.0",
    description="SMTP email sending, templates, campaign management, and open tracking",
    author="Lumina",
    hooks=["email_sent", "campaign_started", "campaign_completed"],
)

_templates: dict[str, EmailTemplate] = {}
_campaigns: list[EmailCampaign] = []
_storage_path = "email_plugin_data.json"
_smtp_config: dict = {}


def on_load() -> None:
    _load_data()
    log.info("Email Automation plugin loaded")


def on_unload() -> None:
    _save_data()


def on_enable() -> None:
    log.info("Email Automation enabled")


def on_disable() -> None:
    log.info("Email Automation disabled")


def _load_data() -> None:
    global _templates, _campaigns, _smtp_config
    if not os.path.exists(_storage_path):
        return
    try:
        with open(_storage_path) as f:
            data = json.load(f)
        _templates = {k: EmailTemplate(**v) for k, v in data.get("templates", {}).items()}
        _campaigns = [EmailCampaign(**c) for c in data.get("campaigns", [])]
        _smtp_config = data.get("smtp", {})
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        log.error("Failed to load email data: %s", e)


def _save_data() -> None:
    with open(_storage_path, "w") as f:
        json.dump(
            {
                "templates": {
                    k: {
                        "name": t.name,
                        "subject": t.subject,
                        "body": t.body,
                        "is_html": t.is_html,
                        "variables": t.variables,
                    }
                    for k, t in _templates.items()
                },
                "campaigns": [
                    {
                        "name": c.name,
                        "template": c.template,
                        "recipients": c.recipients,
                        "sent": c.sent,
                        "failed": c.failed,
                        "opened": c.opened,
                        "status": c.status,
                    }
                    for c in _campaigns
                ],
                "smtp": _smtp_config,
            },
            f,
            indent=2,
        )


def get_smtp_config() -> dict:
    return dict(_smtp_config)


def configure_smtp(
    host: str,
    port: int,
    username: str,
    password: str,
    use_tls: bool = True,
) -> None:
    _smtp_config.update(
        {"host": host, "port": port, "username": username, "password": password, "use_tls": use_tls}
    )
    _save_data()
    log.info("SMTP configured: %s:%d", host, port)


def create_template(
    name: str,
    subject: str,
    body: str,
    is_html: bool = False,
) -> EmailTemplate:
    variables = list(set(re.findall(r"\{(\w+)\}", body)))
    template = EmailTemplate(
        name=name,
        subject=subject,
        body=body,
        is_html=is_html,
        variables=variables,
    )
    _templates[name] = template
    _save_data()
    return template


def delete_template(name: str) -> bool:
    if name in _templates:
        del _templates[name]
        _save_data()
        return True
    return False


def get_template(name: str) -> EmailTemplate | None:
    return _templates.get(name)


def list_templates() -> list[EmailTemplate]:
    return list(_templates.values())


def render_template(template: EmailTemplate, variables: dict[str, str]) -> tuple[str, str]:
    subject, body = template.subject, template.body
    for key, value in variables.items():
        subject = subject.replace(f"{{{key}}}", value)
        body = body.replace(f"{{{key}}}", value)
    return subject, body


def create_campaign(name: str, template_name: str, recipients: list[str]) -> EmailCampaign:
    campaign = EmailCampaign(name=name, template=template_name, recipients=recipients)
    _campaigns.append(campaign)
    _save_data()
    return campaign


def delete_campaign(name: str) -> bool:
    for i, c in enumerate(_campaigns):
        if c.name == name:
            _campaigns.pop(i)
            _save_data()
            return True
    return False


def list_campaigns() -> list[EmailCampaign]:
    return list(_campaigns)


def send_email(to: str, subject: str, body: str, is_html: bool = False) -> bool:
    if not _smtp_config.get("host"):
        log.error("SMTP not configured")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = _smtp_config["username"]
        msg["To"] = to
        if is_html:
            msg.attach(MIMEText(body, "html"))
        else:
            msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP(_smtp_config["host"], _smtp_config["port"]) as server:
            if _smtp_config.get("use_tls", True):
                server.starttls()
            server.login(_smtp_config["username"], _smtp_config["password"])
            server.send_message(msg)
        log.info("Email sent to %s: %s", to, subject[:50])
        return True
    except Exception as e:
        log.error("Failed to send email to %s: %s", to, e)
        return False


async def run_campaign(campaign_name: str) -> dict:
    for c in _campaigns:
        if c.name == campaign_name and c.status == "draft":
            c.status = "running"
            template = _templates.get(c.template)
            if not template:
                c.status = "failed"
                _save_data()
                return {"error": f"Template '{c.template}' not found"}
            for recipient in c.recipients:
                ok = send_email(recipient, template.subject, template.body, template.is_html)
                if ok:
                    c.sent += 1
                else:
                    c.failed += 1
            c.status = "completed"
            _save_data()
            return {"name": c.name, "sent": c.sent, "failed": c.failed, "status": c.status}
    return {"error": "Campaign not found"}


def import_recipients(campaign_name: str, csv_path: str, email_column: str = "email") -> int:
    for c in _campaigns:
        if c.name == campaign_name:
            count = 0
            with open(csv_path, newline="") as f:
                for row in csv.DictReader(f):
                    email = row.get(email_column, "").strip()
                    if email and email not in c.recipients:
                        c.recipients.append(email)
                        count += 1
            _save_data()
            return count
    return 0
