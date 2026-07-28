from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any

import httpx

_WORKFLOWS_DIR = os.path.expanduser("~/.lumina/workflows")

WORKFLOW_CATEGORIES = [
    "automation", "data", "communication", "development", "crm", "ecommerce", "custom"
]

NODE_TYPE_MAP = {
    "trigger": "n8n-nodes-base.webhook",
    "schedule": "n8n-nodes-base.scheduleTrigger",
    "manual": "n8n-nodes-base.manualTrigger",
    "action": "n8n-nodes-base.set",
    "condition": "n8n-nodes-base.if",
    "api_call": "n8n-nodes-base.httpRequest",
    "message": "n8n-nodes-base.emailSend",
    "notification": "n8n-nodes-base.slack",
    "delay": "n8n-nodes-base.wait",
    "data": "n8n-nodes-base.code",
    "transform": "n8n-nodes-base.function",
    "email": "n8n-nodes-base.emailSend",
    "slack": "n8n-nodes-base.slack",
}

REVERSE_NODE_MAP = {v: k for k, v in NODE_TYPE_MAP.items()}

N8N_TEMPLATES = [
    {
        "id": "tmpl-webhook-ai",
        "name": "Webhook \u2192 AI Response",
        "description": "Receive webhook, process with AI, return response",
        "category": "automation",
        "tags": ["webhook", "ai", "api"],
        "nodes": [
            {"id": "n1", "type": "trigger", "label": "Webhook Trigger", "config": {"method": "POST", "path": "/ai-webhook"}, "position": {"x": 40, "y": 80}},
            {"id": "n2", "type": "api_call", "label": "Call AI Engine", "config": {"url": "/api/chat", "method": "POST", "body": "{{$json.body}}"}, "position": {"x": 280, "y": 80}},
            {"id": "n3", "type": "action", "label": "Return Response", "config": {"response": "{{$json.result}}"}, "position": {"x": 520, "y": 80}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
        ],
    },
    {
        "id": "tmpl-schedule-email",
        "name": "Scheduled Email Report",
        "description": "Daily schedule \u2192 gather data \u2192 send email report",
        "category": "communication",
        "tags": ["schedule", "email", "report"],
        "nodes": [
            {"id": "n1", "type": "schedule", "label": "Daily Schedule", "config": {"cron": "0 8 * * *"}, "position": {"x": 40, "y": 80}},
            {"id": "n2", "type": "api_call", "label": "Fetch Analytics", "config": {"url": "/api/analytics/dashboard", "method": "GET"}, "position": {"x": 280, "y": 80}},
            {"id": "n3", "type": "data", "label": "Format Report", "config": {"template": "daily_report"}, "position": {"x": 280, "y": 200}},
            {"id": "n4", "type": "message", "label": "Send Email", "config": {"to": "{{$json.email}}", "subject": "Daily Report"}, "position": {"x": 520, "y": 140}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
            {"id": "e3", "source": "n3", "target": "n4"},
        ],
    },
    {
        "id": "tmpl-lead-scraper",
        "name": "Lead Scraper & Enrich",
        "description": "Scrape leads \u2192 enrich with AI \u2192 save to CRM",
        "category": "crm",
        "tags": ["leads", "crm", "enrichment", "ai"],
        "nodes": [
            {"id": "n1", "type": "manual", "label": "Manual Trigger", "config": {}, "position": {"x": 40, "y": 80}},
            {"id": "n2", "type": "api_call", "label": "Run Lead Gen", "config": {"url": "/api/lead-gen/generate", "method": "POST"}, "position": {"x": 280, "y": 80}},
            {"id": "n3", "type": "condition", "label": "Has Email?", "config": {"field": "email", "operator": "exists"}, "position": {"x": 280, "y": 200}},
            {"id": "n4", "type": "api_call", "label": "AI Enrich", "config": {"url": "/api/lead-gen/ai-score", "method": "POST"}, "position": {"x": 520, "y": 80}},
            {"id": "n5", "type": "message", "label": "Notify", "config": {"message": "{{$json.leads_saved}} leads saved"}, "position": {"x": 520, "y": 200}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
            {"id": "e3", "source": "n3", "target": "n4"},
            {"id": "e4", "source": "n3", "target": "n5"},
        ],
    },
    {
        "id": "tmpl-slack-alert",
        "name": "System Alert \u2192 Slack",
        "description": "Monitor system health and send alerts to Slack",
        "category": "development",
        "tags": ["monitoring", "slack", "alerts", "devops"],
        "nodes": [
            {"id": "n1", "type": "trigger", "label": "Webhook Alert", "config": {"method": "POST", "path": "/alert"}, "position": {"x": 40, "y": 80}},
            {"id": "n2", "type": "condition", "label": "Is Critical?", "config": {"field": "level", "operator": "eq", "value": "critical"}, "position": {"x": 280, "y": 80}},
            {"id": "n3", "type": "slack", "label": "Slack Message", "config": {"channel": "#alerts", "text": "{{$json.message}}"}, "position": {"x": 520, "y": 80}},
            {"id": "n4", "type": "delay", "label": "Wait 5min", "config": {"seconds": 300}, "position": {"x": 280, "y": 200}},
            {"id": "n5", "type": "action", "label": "Log to Audit", "config": {"action": "alert_sent"}, "position": {"x": 520, "y": 200}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
            {"id": "e3", "source": "n2", "target": "n4"},
            {"id": "e4", "source": "n4", "target": "n5"},
        ],
    },
    {
        "id": "tmpl-social-post",
        "name": "Social Media Post Scheduler",
        "description": "Schedule and publish posts across social platforms",
        "category": "automation",
        "tags": ["social", "scheduler", "publishing"],
        "nodes": [
            {"id": "n1", "type": "schedule", "label": "Post Schedule", "config": {"cron": "0 9,15 * * *"}, "position": {"x": 40, "y": 80}},
            {"id": "n2", "type": "data", "label": "Load Post Queue", "config": {"source": "~/.lumina/social/queue.json"}, "position": {"x": 280, "y": 80}},
            {"id": "n3", "type": "condition", "label": "Has Queue?", "config": {"field": "posts", "operator": "exists"}, "position": {"x": 280, "y": 200}},
            {"id": "n4", "type": "api_call", "label": "Post to Twitter", "config": {"url": "/api/social/twitter/post", "method": "POST"}, "position": {"x": 520, "y": 80}},
            {"id": "n5", "type": "api_call", "label": "Post to LinkedIn", "config": {"url": "/api/social/linkedin/post", "method": "POST"}, "position": {"x": 520, "y": 200}},
            {"id": "n6", "type": "action", "label": "Mark Posted", "config": {"action": "mark_posted"}, "position": {"x": 760, "y": 140}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
            {"id": "e3", "source": "n3", "target": "n4"},
            {"id": "e4", "source": "n3", "target": "n5"},
            {"id": "e5", "source": "n4", "target": "n6"},
            {"id": "e6", "source": "n5", "target": "n6"},
        ],
    },
    {
        "id": "tmpl-ecommerce-order",
        "name": "E-commerce Order Processor",
        "description": "New order \u2192 validate \u2192 process payment \u2192 notify customer",
        "category": "ecommerce",
        "tags": ["orders", "payment", "notifications", "ecommerce"],
        "nodes": [
            {"id": "n1", "type": "trigger", "label": "New Order Webhook", "config": {"method": "POST", "path": "/order/new"}, "position": {"x": 40, "y": 80}},
            {"id": "n2", "type": "condition", "label": "Payment Valid?", "config": {"field": "payment.status", "operator": "eq", "value": "confirmed"}, "position": {"x": 280, "y": 80}},
            {"id": "n3", "type": "action", "label": "Fulfill Order", "config": {"action": "fulfill", "provider": "{{$json.shipping.provider}}"}, "position": {"x": 520, "y": 80}},
            {"id": "n4", "type": "email", "label": "Send Confirmation", "config": {"to": "{{$json.customer.email}}", "subject": "Order Confirmed"}, "position": {"x": 520, "y": 200}},
            {"id": "n5", "type": "notification", "label": "Slack Alert Team", "config": {"channel": "#orders", "text": "New order: {{$json.id}}"}, "position": {"x": 760, "y": 140}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
            {"id": "e3", "source": "n2", "target": "n4"},
            {"id": "e4", "source": "n3", "target": "n5"},
            {"id": "e5", "source": "n4", "target": "n5"},
        ],
    },
    {
        "id": "tmpl-multi-notify",
        "name": "Multi-channel Notifier",
        "description": "Send alerts to email + Slack + Telegram simultaneously",
        "category": "communication",
        "tags": ["notification", "multi-channel", "slack", "email"],
        "nodes": [
            {"id": "n1", "type": "trigger", "label": "Alert Webhook", "config": {"method": "POST", "path": "/notify"}, "position": {"x": 40, "y": 80}},
            {"id": "n2", "type": "email", "label": "Send Email", "config": {"to": "admin@lumina.local", "subject": "Alert: {{$json.title}}"}, "position": {"x": 280, "y": 40}},
            {"id": "n3", "type": "slack", "label": "Slack Message", "config": {"channel": "#alerts", "text": "{{$json.message}}"}, "position": {"x": 280, "y": 140}},
            {"id": "n4", "type": "notification", "label": "Telegram Bot", "config": {"platform": "telegram", "message": "[{{$json.level}}] {{$json.message}}"}, "position": {"x": 280, "y": 240}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n1", "target": "n3"},
            {"id": "e3", "source": "n1", "target": "n4"},
        ],
    },
    {
        "id": "tmpl-data-backup",
        "name": "Data Backup & Sync",
        "description": "Periodic database backup \u2192 compress \u2192 upload to cloud storage",
        "category": "data",
        "tags": ["backup", "database", "cloud", "sync"],
        "nodes": [
            {"id": "n1", "type": "schedule", "label": "Backup Schedule", "config": {"cron": "0 2 * * *"}, "position": {"x": 40, "y": 80}},
            {"id": "n2", "type": "api_call", "label": "Dump Database", "config": {"url": "/api/system/db-dump", "method": "POST"}, "position": {"x": 280, "y": 80}},
            {"id": "n3", "type": "data", "label": "Compress Archive", "config": {"operation": "compress"}, "position": {"x": 280, "y": 200}},
            {"id": "n4", "type": "api_call", "label": "Upload to S3", "config": {"url": "/api/storage/upload", "method": "POST"}, "position": {"x": 520, "y": 140}},
            {"id": "n5", "type": "action", "label": "Cleanup Old Backups", "config": {"action": "cleanup", "retention_days": 30}, "position": {"x": 760, "y": 140}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
            {"id": "e3", "source": "n3", "target": "n4"},
            {"id": "e4", "source": "n4", "target": "n5"},
        ],
    },
    {
        "id": "tmpl-cicd-pipeline",
        "name": "CI/CD Pipeline Monitor",
        "description": "Check build status \u2192 notify team on failure \u2192 auto-retry",
        "category": "development",
        "tags": ["ci-cd", "monitoring", "github", "deployment"],
        "nodes": [
            {"id": "n1", "type": "trigger", "label": "GitHub Webhook", "config": {"method": "POST", "path": "/github/action"}, "position": {"x": 40, "y": 80}},
            {"id": "n2", "type": "condition", "label": "Build Failed?", "config": {"field": "action.status", "operator": "eq", "value": "failure"}, "position": {"x": 280, "y": 80}},
            {"id": "n3", "type": "slack", "label": "Alert #dev-team", "config": {"channel": "#dev-team", "text": "Build failed: {{$json.action.name}}"}, "position": {"x": 520, "y": 80}},
            {"id": "n4", "type": "action", "label": "Auto-Retry Build", "config": {"action": "retry_build", "workflow": "{{$json.action.name}}"}, "position": {"x": 520, "y": 200}},
            {"id": "n5", "type": "delay", "label": "Wait 10min", "config": {"seconds": 600}, "position": {"x": 520, "y": 320}},
            {"id": "n6", "type": "action", "label": "Log Outcome", "config": {"action": "log"}, "position": {"x": 760, "y": 200}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
            {"id": "e3", "source": "n2", "target": "n4"},
            {"id": "e4", "source": "n4", "target": "n5"},
            {"id": "e5", "source": "n5", "target": "n6"},
        ],
    },
    {
        "id": "tmpl-crm-sync",
        "name": "CRM Contact Sync",
        "description": "Sync new contacts from web forms \u2192 enrich \u2192 push to CRM",
        "category": "crm",
        "tags": ["crm", "contacts", "sync", "enrichment"],
        "nodes": [
            {"id": "n1", "type": "trigger", "label": "Form Webhook", "config": {"method": "POST", "path": "/form/contact"}, "position": {"x": 40, "y": 80}},
            {"id": "n2", "type": "condition", "label": "Valid Contact?", "config": {"field": "email", "operator": "exists"}, "position": {"x": 280, "y": 80}},
            {"id": "n3", "type": "api_call", "label": "Enrich with AI", "config": {"url": "/api/crm/enrich", "method": "POST"}, "position": {"x": 520, "y": 80}},
            {"id": "n4", "type": "api_call", "label": "Push to CRM", "config": {"url": "/api/crm/contacts", "method": "POST"}, "position": {"x": 520, "y": 200}},
            {"id": "n5", "type": "email", "label": "Welcome Email", "config": {"to": "{{$json.email}}", "subject": "Welcome to Lumina!"}, "position": {"x": 760, "y": 140}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
            {"id": "e3", "source": "n2", "target": "n4"},
            {"id": "e4", "source": "n3", "target": "n5"},
            {"id": "e5", "source": "n4", "target": "n5"},
        ],
    },
    {
        "id": "tmpl-code-review",
        "name": "Code Review Reminder",
        "description": "Check open PRs \u2192 ping reviewers who haven't reviewed yet",
        "category": "development",
        "tags": ["github", "pr", "code-review", "reminder"],
        "nodes": [
            {"id": "n1", "type": "schedule", "label": "Daily Check", "config": {"cron": "0 10,15 * * 1-5"}, "position": {"x": 40, "y": 80}},
            {"id": "n2", "type": "api_call", "label": "Fetch Open PRs", "config": {"url": "/api/github/pulls", "method": "GET"}, "position": {"x": 280, "y": 80}},
            {"id": "n3", "type": "condition", "label": "PRs Pending Review?", "config": {"field": "pulls", "operator": "exists"}, "position": {"x": 280, "y": 200}},
            {"id": "n4", "type": "slack", "label": "Remind Reviewers", "config": {"channel": "#code-reviews", "text": "Pending PRs: {{$json.pulls.length}} need review"}, "position": {"x": 520, "y": 140}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
            {"id": "e3", "source": "n3", "target": "n4"},
        ],
    },
    {
        "id": "tmpl-content-approval",
        "name": "Content Approval Workflow",
        "description": "Submit content \u2192 manager approves/rejects \u2192 publish or revise",
        "category": "custom",
        "tags": ["content", "approval", "workflow", "publishing"],
        "nodes": [
            {"id": "n1", "type": "trigger", "label": "Content Submitted", "config": {"method": "POST", "path": "/content/submit"}, "position": {"x": 40, "y": 80}},
            {"id": "n2", "type": "slack", "label": "Notify Manager", "config": {"channel": "@manager", "text": "Content needs approval: {{$json.title}}"}, "position": {"x": 280, "y": 80}},
            {"id": "n3", "type": "condition", "label": "Approved?", "config": {"field": "decision", "operator": "eq", "value": "approved"}, "position": {"x": 280, "y": 200}},
            {"id": "n4", "type": "action", "label": "Publish Content", "config": {"action": "publish", "platform": "all"}, "position": {"x": 520, "y": 80}},
            {"id": "n5", "type": "action", "label": "Send for Revision", "config": {"action": "request_revision", "feedback": "{{$json.feedback}}"}, "position": {"x": 520, "y": 200}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
            {"id": "e3", "source": "n3", "target": "n4"},
            {"id": "e4", "source": "n3", "target": "n5"},
        ],
    },
    {
        "id": "tmpl-invoice-gen",
        "name": "Invoice Generator",
        "description": "New order \u2192 generate PDF invoice \u2192 email to customer \u2192 archive",
        "category": "ecommerce",
        "tags": ["invoice", "pdf", "email", "billing"],
        "nodes": [
            {"id": "n1", "type": "trigger", "label": "Order Paid Webhook", "config": {"method": "POST", "path": "/order/paid"}, "position": {"x": 40, "y": 80}},
            {"id": "n2", "type": "api_call", "label": "Generate PDF", "config": {"url": "/api/invoice/generate", "method": "POST"}, "position": {"x": 280, "y": 80}},
            {"id": "n3", "type": "email", "label": "Email Invoice", "config": {"to": "{{$json.customer.email}}", "subject": "Invoice #{{$json.order.id}}", "attachment": "invoice.pdf"}, "position": {"x": 520, "y": 80}},
            {"id": "n4", "type": "action", "label": "Archive Record", "config": {"action": "archive", "bucket": "invoices"}, "position": {"x": 760, "y": 80}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
            {"id": "e3", "source": "n3", "target": "n4"},
        ],
    },
    {
        "id": "tmpl-server-health",
        "name": "Server Health Monitor",
        "description": "Ping servers \u2192 check response time \u2192 alert if down or slow",
        "category": "development",
        "tags": ["monitoring", "uptime", "health", "devops"],
        "nodes": [
            {"id": "n1", "type": "schedule", "label": "Every 5min", "config": {"cron": "*/5 * * * *"}, "position": {"x": 40, "y": 80}},
            {"id": "n2", "type": "api_call", "label": "Ping Server 1", "config": {"url": "https://app.lumina.local/healthz", "method": "GET"}, "position": {"x": 280, "y": 40}},
            {"id": "n3", "type": "api_call", "label": "Ping Server 2", "config": {"url": "https://api.lumina.local/healthz", "method": "GET"}, "position": {"x": 280, "y": 140}},
            {"id": "n4", "type": "condition", "label": "All Healthy?", "config": {"field": "status", "operator": "eq", "value": "ok"}, "position": {"x": 520, "y": 80}},
            {"id": "n5", "type": "action", "label": "Log Health OK", "config": {"action": "log", "level": "info"}, "position": {"x": 760, "y": 40}},
            {"id": "n6", "type": "slack", "label": "Alert on Failure", "config": {"channel": "#devops", "text": "Server DOWN: {{$json.server}}"}, "position": {"x": 760, "y": 140}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n1", "target": "n3"},
            {"id": "e3", "source": "n2", "target": "n4"},
            {"id": "e4", "source": "n3", "target": "n4"},
            {"id": "e5", "source": "n4", "target": "n5"},
            {"id": "e6", "source": "n4", "target": "n6"},
        ],
    },
    {
        "id": "tmpl-social-monitor",
        "name": "Social Mention Tracker",
        "description": "Track brand mentions \u2192 classify sentiment \u2192 alert on negative",
        "category": "automation",
        "tags": ["social", "monitoring", "sentiment", "brand"],
        "nodes": [
            {"id": "n1", "type": "schedule", "label": "Every Hour", "config": {"cron": "0 * * * *"}, "position": {"x": 40, "y": 80}},
            {"id": "n2", "type": "api_call", "label": "Fetch Mentions", "config": {"url": "/api/social/mentions", "method": "GET"}, "position": {"x": 280, "y": 80}},
            {"id": "n3", "type": "api_call", "label": "Classify Sentiment", "config": {"url": "/api/ai/sentiment", "method": "POST"}, "position": {"x": 280, "y": 200}},
            {"id": "n4", "type": "condition", "label": "Negative?", "config": {"field": "sentiment", "operator": "eq", "value": "negative"}, "position": {"x": 520, "y": 140}},
            {"id": "n5", "type": "slack", "label": "Alert Team", "config": {"channel": "#social", "text": "Negative mention: {{$json.mention.text}}"}, "position": {"x": 760, "y": 80}},
            {"id": "n6", "type": "action", "label": "Log Tracked", "config": {"action": "log", "level": "info"}, "position": {"x": 760, "y": 200}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
            {"id": "e3", "source": "n3", "target": "n4"},
            {"id": "e4", "source": "n4", "target": "n5"},
            {"id": "e5", "source": "n4", "target": "n6"},
        ],
    },
]


class WorkflowNode:
    def __init__(
        self,
        node_type: str,
        label: str,
        config: dict[str, Any] | None = None,
        position: dict[str, float] | None = None,
        node_id: str | None = None,
    ):
        self.id = node_id or uuid.uuid4().hex[:8]
        self.type = node_type
        self.label = label
        self.config = config or {}
        self.position = position or {"x": 0, "y": 0}

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "label": self.label,
            "config": self.config,
            "position": self.position,
        }

    @classmethod
    def from_dict(cls, d: dict) -> WorkflowNode:
        return cls(
            node_id=d.get("id"),
            node_type=d["type"],
            label=d.get("label", ""),
            config=d.get("config", {}),
            position=d.get("position", {"x": 0, "y": 0}),
        )


class WorkflowEdge:
    def __init__(self, source: str, target: str, edge_id: str | None = None, label: str = ""):
        self.id = edge_id or uuid.uuid4().hex[:8]
        self.source = source
        self.target = target
        self.label = label

    def to_dict(self) -> dict:
        return {"id": self.id, "source": self.source, "target": self.target, "label": self.label}

    @classmethod
    def from_dict(cls, d: dict) -> WorkflowEdge:
        return cls(
            edge_id=d.get("id"),
            source=d["source"],
            target=d["target"],
            label=d.get("label", ""),
        )


class Workflow:
    def __init__(
        self,
        name: str,
        description: str = "",
        category: str = "custom",
        workflow_id: str | None = None,
        created_at: float | None = None,
        updated_at: float | None = None,
    ):
        self.id = workflow_id or uuid.uuid4().hex[:12]
        self.name = name
        self.description = description
        self.category = category if category in WORKFLOW_CATEGORIES else "custom"
        self.nodes: list[WorkflowNode] = []
        self.edges: list[WorkflowEdge] = []
        self.created_at = created_at or time.time()
        self.updated_at = updated_at or time.time()

    def add_node(self, node: WorkflowNode) -> str:
        self.nodes.append(node)
        self.updated_at = time.time()
        return node.id

    def update_node(self, node_id: str, **kwargs) -> WorkflowNode | None:
        for node in self.nodes:
            if node.id == node_id:
                for k, v in kwargs.items():
                    if k == "config":
                        node.config.update(v)
                    elif hasattr(node, k):
                        setattr(node, k, v)
                self.updated_at = time.time()
                return node
        return None

    def remove_node(self, node_id: str) -> bool:
        self.nodes = [n for n in self.nodes if n.id != node_id]
        self.edges = [e for e in self.edges if e.source != node_id and e.target != node_id]
        self.updated_at = time.time()
        return True

    def add_edge(self, edge: WorkflowEdge) -> str:
        self.edges.append(edge)
        self.updated_at = time.time()
        return edge.id

    def remove_edge(self, edge_id: str) -> bool:
        self.edges = [e for e in self.edges if e.id != edge_id]
        self.updated_at = time.time()
        return True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Workflow:
        wf = cls(
            name=d["name"],
            description=d.get("description", ""),
            category=d.get("category", "custom"),
            workflow_id=d.get("id"),
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at"),
        )
        wf.nodes = [WorkflowNode.from_dict(n) for n in d.get("nodes", [])]
        wf.edges = [WorkflowEdge.from_dict(e) for e in d.get("edges", [])]
        return wf


class WorkflowExecutionError(Exception):
    pass


class WorkflowStore:
    def __init__(self):
        self._workflows: list[Workflow] = []
        self._load()

    def _path(self, name: str) -> str:
        os.makedirs(_WORKFLOWS_DIR, exist_ok=True)
        return os.path.join(_WORKFLOWS_DIR, name)

    def _templates_path(self) -> str:
        return self._path("templates.json")

    def _load(self) -> None:
        path = self._path("workflows.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    self._workflows = [Workflow.from_dict(d) for d in json.load(f)]
            except Exception:
                self._workflows = []

    def _save(self) -> None:
        with open(self._path("workflows.json"), "w") as f:
            json.dump([w.to_dict() for w in self._workflows], f, indent=2)

    def create(self, name: str, description: str = "", category: str = "custom") -> Workflow:
        wf = Workflow(name=name, description=description, category=category)
        self._workflows.append(wf)
        self._save()
        return wf

    def list(self, category: str | None = None) -> list[Workflow]:
        if category:
            return [w for w in self._workflows if w.category == category]
        return sorted(self._workflows, key=lambda w: w.updated_at, reverse=True)

    def get(self, workflow_id: str) -> Workflow | None:
        for w in self._workflows:
            if w.id == workflow_id:
                return w
        return None

    def update(self, workflow_id: str, **kwargs) -> Workflow | None:
        wf = self.get(workflow_id)
        if not wf:
            return None
        for k, v in kwargs.items():
            if hasattr(wf, k):
                setattr(wf, k, v)
        wf.updated_at = time.time()
        self._save()
        return wf

    def delete(self, workflow_id: str) -> bool:
        for i, w in enumerate(self._workflows):
            if w.id == workflow_id:
                self._workflows.pop(i)
                self._save()
                return True
        return False


    # ── n8n Integration ──

    def to_n8n_json(self, workflow_id: str) -> dict | None:
        wf = self.get(workflow_id)
        if not wf:
            return None
        n8n_nodes = []
        n8n_connections: dict[str, Any] = {}
        for node in wf.nodes:
            nid = node.id
            n8n_nodes.append({
                "id": nid,
                "name": node.label,
                "type": _to_n8n_type(node.type),
                "typeVersion": 1,
                "position": [node.position.get("x", 0), node.position.get("y", 0)],
                "parameters": node.config,
            })
            n8n_connections[nid] = {"main": [[]]}
        edge_map: dict[str, list[str]] = {}
        for edge in wf.edges:
            edge_map.setdefault(edge.source, []).append(edge.target)
        for src, targets in edge_map.items():
            if src in n8n_connections:
                for tgt in targets:
                    idx = [n["id"] for n in n8n_nodes].index(tgt) if tgt in [n["id"] for n in n8n_nodes] else -1
                    if idx >= 0:
                        n8n_connections[src]["main"][0].append({"node": tgt, "type": "main", "index": 0})
        for node in n8n_nodes:
            nid = node["id"]
            node["connections"] = n8n_connections.get(nid, {"main": [[]]})
        return {
            "name": wf.name,
            "nodes": n8n_nodes,
            "connections": {nid: nid_c for nid, nid_c in n8n_connections.items() if nid_c["main"][0]},
            "settings": {"executionOrder": "v1"},
            "id": wf.id,
            "tags": [],
        }

    def from_n8n_json(self, n8n_data: dict, name: str | None = None) -> Workflow:
        wf = Workflow(name=name or n8n_data.get("name", "Imported n8n"), category="custom")
        id_map: dict[str, str] = {}
        for n in n8n_data.get("nodes", []):
            orig_id = n.get("id", uuid.uuid4().hex[:8])
            new_id = uuid.uuid4().hex[:8]
            id_map[orig_id] = new_id
            node = WorkflowNode(
                node_id=new_id,
                node_type=_to_lumina_type(n.get("type", "action")),
                label=n.get("name", "Node"),
                config=n.get("parameters", {}),
                position={"x": n.get("position", [0, 0])[0], "y": n.get("position", [0, 0])[1]},
            )
            wf.add_node(node)
        for n in n8n_data.get("nodes", []):
            orig_id = n.get("id", "")
            for conn_list in n.get("connections", {}).get("main", []):
                for conn in conn_list:
                    target_orig = conn.get("node", "")
                    if orig_id in id_map and target_orig in id_map:
                        edge = WorkflowEdge(source=id_map[orig_id], target=id_map[target_orig])
                        wf.add_edge(edge)
        return wf

    def get_n8n_templates(self, category: str | None = None, query: str = "") -> list[dict]:
        templates = list(N8N_TEMPLATES)
        custom = self._load_custom_templates()
        templates.extend(custom)
        if category:
            templates = [t for t in templates if t["category"] == category]
        if query:
            q = query.lower()
            templates = [
                t for t in templates
                if q in t["name"].lower() or q in t["description"].lower() or any(q in tag.lower() for tag in t.get("tags", []))
            ]
        return templates

    def _load_custom_templates(self) -> list[dict]:
        path = self._templates_path()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_custom_templates(self, templates: list[dict]) -> None:
        with open(self._templates_path(), "w") as f:
            json.dump(templates, f, indent=2)

    def save_as_template(self, workflow_id: str, tags: list[str] | None = None) -> dict | None:
        wf = self.get(workflow_id)
        if not wf:
            return None
        tmpl = {
            "id": f"custom-{uuid.uuid4().hex[:8]}",
            "name": wf.name,
            "description": wf.description,
            "category": wf.category,
            "tags": tags or [],
            "nodes": [n.to_dict() for n in wf.nodes],
            "edges": [e.to_dict() for e in wf.edges],
        }
        custom = self._load_custom_templates()
        custom.append(tmpl)
        self._save_custom_templates(custom)
        return tmpl

    def delete_custom_template(self, template_id: str) -> bool:
        custom = self._load_custom_templates()
        before = len(custom)
        custom = [t for t in custom if t["id"] != template_id]
        if len(custom) == before:
            return False
        self._save_custom_templates(custom)
        return True

    def import_n8n_template(self, template_id: str) -> Workflow | None:
        all_templates = list(N8N_TEMPLATES) + self._load_custom_templates()
        tmpl = next((t for t in all_templates if t["id"] == template_id), None)
        if not tmpl:
            return None
        wf = Workflow(name=tmpl["name"], description=tmpl["description"], category=tmpl["category"])
        id_map: dict[str, str] = {}
        for n in tmpl.get("nodes", []):
            orig_id = n["id"]
            new_id = uuid.uuid4().hex[:8]
            id_map[orig_id] = new_id
            node = WorkflowNode(
                node_id=new_id, node_type=n["type"], label=n["label"],
                config=n.get("config", {}), position=n.get("position", {"x": 0, "y": 0}),
            )
            wf.add_node(node)
        for e in tmpl.get("edges", []):
            if e["source"] in id_map and e["target"] in id_map:
                wf.add_edge(WorkflowEdge(source=id_map[e["source"]], target=id_map[e["target"]]))
        self._workflows.append(wf)
        self._save()
        return wf

    async def check_n8n_health(self) -> dict:
        return {"online": False, "url": "", "note": "Use export/import instead of live connection"}

    async def push_to_n8n(self, workflow_id: str) -> dict:
        return {"success": False, "error": "Live push not available — export as JSON and import manually into n8n"}

    async def execute_on_n8n(self, workflow_id: str) -> dict:
        return {"success": False, "error": "Live execution not available — export as JSON and run in n8n"}

    async def install_n8n(self) -> dict:
        return {"success": False, "error": "n8n is not bundled — install separately with: npm install -g n8n"}

    async def get_n8n_workflows(self) -> dict:
        return {"success": False, "error": "Remote n8n workflows not available — use templates and import/export instead"}


    # ── Workflow Execution Engine ──

    def execute_workflow(self, workflow_id: str, payload: dict | None = None) -> dict:
        wf = self.get(workflow_id)
        if not wf:
            return {"success": False, "error": "Workflow not found"}
        if not wf.nodes:
            return {"success": False, "error": "Workflow has no nodes"}

        triggers = [n for n in wf.nodes if n.type in ("trigger", "schedule", "manual")]
        if not triggers:
            return {"success": False, "error": "No trigger node found — add a trigger, schedule, or manual node"}

        data = payload or {}
        outputs: dict[str, Any] = {}
        visited: set[str] = set()
        errors: list[str] = []

        edge_map: dict[str, list[str]] = {}
        for e in wf.edges:
            edge_map.setdefault(e.source, []).append(e.target)

        def get_node_label(nid: str) -> str:
            n = next((x for x in wf.nodes if x.id == nid), None)
            return n.label if n else nid

        def follow(node_id: str, input_data: dict) -> None:
            if node_id in visited:
                return
            visited.add(node_id)

            node = next((n for n in wf.nodes if n.id == node_id), None)
            if not node:
                return

            try:
                result = _execute_node(node, input_data)
            except WorkflowExecutionError as e:
                errors.append(f"[{get_node_label(node_id)}] {e}")
                outputs[node_id] = {"status": "error", "error": str(e), "type": node.type, "label": node.label}
                return
            except Exception as e:
                errors.append(f"[{get_node_label(node_id)}] Unexpected error: {e}")
                outputs[node_id] = {"status": "error", "error": str(e), "type": node.type, "label": node.label}
                return

            outputs[node_id] = {"status": "ok", "output": result, "type": node.type, "label": node.label}

            if node.type == "condition":
                truthy = bool(result.get("result", False))
                targets = edge_map.get(node_id, [])
                if truthy and targets:
                    follow(targets[0], result)
                elif not truthy and len(targets) > 1:
                    follow(targets[1], result)
            elif node.type == "delay":
                import asyncio
                seconds = node.config.get("seconds", 1)
                try:
                    asyncio.run(asyncio.sleep(seconds))
                except RuntimeError:
                    time.sleep(seconds)
                for t in edge_map.get(node_id, []):
                    follow(t, result)
            else:
                for t in edge_map.get(node_id, []):
                    follow(t, result)

        for trigger in triggers:
            follow(trigger.id, data)

        return {
            "success": len(errors) == 0,
            "errors": errors,
            "outputs": outputs,
            "node_count": len(visited),
            "total_nodes": len(wf.nodes),
        }


def _to_n8n_type(lumina_type: str) -> str:
    if lumina_type in NODE_TYPE_MAP:
        return NODE_TYPE_MAP[lumina_type]
    return f"n8n-nodes-base.{lumina_type}"


def _to_lumina_type(n8n_type: str) -> str:
    if n8n_type in REVERSE_NODE_MAP:
        return REVERSE_NODE_MAP[n8n_type]
    if n8n_type.startswith("n8n-nodes-base."):
        suffix = n8n_type.split(".")[-1]
        if suffix in NODE_TYPE_MAP:
            return suffix
        return suffix
    return "action"


def _execute_node(node: WorkflowNode, input_data: dict) -> dict:
    import re

    def resolve(template: str, data: dict) -> Any:
        def replacer(m):
            expr = m.group(1).strip()
            keys = expr.split(".")
            val = data
            for k in keys:
                if isinstance(val, dict):
                    val = val.get(k, "")
                else:
                    return ""
            return str(val) if val is not None else ""
        return re.sub(r"\{\{\s*\$json\.([^}]+)\s*\}\}", replacer, template) if isinstance(template, str) else template

    def resolve_deep(cfg: Any, data: dict) -> Any:
        if isinstance(cfg, str):
            return resolve(cfg, data)
        if isinstance(cfg, dict):
            return {k: resolve_deep(v, data) for k, v in cfg.items()}
        if isinstance(cfg, list):
            return [resolve_deep(v, data) for v in cfg]
        return cfg

    config = resolve_deep(node.config, input_data)

    if node.type == "trigger":
        return {"triggered": True, "payload": input_data}

    if node.type in ("schedule", "manual"):
        return {"triggered": True, "source": node.type, "payload": input_data}

    if node.type == "api_call":
        url = config.get("url", "")
        method = config.get("method", "GET").upper()
        body = config.get("body", None)
        try:
            import httpx
            client_kwargs = {"timeout": 15}
            if isinstance(body, str):
                try:
                    body = json.loads(body)
                except Exception:
                    pass
            if body is not None:
                client_kwargs["json"] = body
            base = os.environ.get("LUMINA_HOST", "http://localhost:8000")
            if url.startswith("/"):
                url = base.rstrip("/") + url
            r = httpx.request(method, url, **client_kwargs)
            return {"status": r.status_code, "body": r.text[:5000], "headers": dict(r.headers)}
        except Exception as e:
            raise WorkflowExecutionError(f"API call failed: {e}") from e

    if node.type == "condition":
        field = config.get("field", "")
        operator = config.get("operator", "exists")
        value = config.get("value", None)
        resolved = input_data
        for key in field.split("."):
            if isinstance(resolved, dict):
                resolved = resolved.get(key, None)
            else:
                resolved = None
                break
        if operator == "exists":
            result = resolved is not None and resolved != ""
        elif operator == "eq":
            result = str(resolved) == str(value)
        elif operator == "neq":
            result = str(resolved) != str(value)
        elif operator == "gt":
            try:
                result = float(resolved) > float(value)
            except (TypeError, ValueError):
                result = False
        elif operator == "lt":
            try:
                result = float(resolved) < float(value)
            except (TypeError, ValueError):
                result = False
        else:
            result = bool(resolved)
        return {"result": result, "field_value": resolved}

    if node.type == "data":
        operation = config.get("operation", "")
        if operation == "compress":
            return {"compressed": True, "original": input_data}
        template = config.get("template", "")
        if template:
            return {"transformed": True, "template": template, "data": input_data}
        source = config.get("source", "")
        if source and os.path.exists(os.path.expanduser(source)):
            try:
                with open(os.path.expanduser(source)) as f:
                    return {"loaded": True, "data": json.load(f), "source": source}
            except Exception:
                pass
        return {"processed": True, "data": input_data}

    if node.type == "transform":
        return {"transformed": True, "input": input_data}

    if node.type in ("message", "email"):
        return {
            "sent": True,
            "to": config.get("to", ""),
            "subject": config.get("subject", ""),
            "message": config.get("message", config.get("body", "")),
        }

    if node.type == "slack":
        return {
            "sent": True,
            "channel": config.get("channel", ""),
            "text": config.get("text", ""),
        }

    if node.type == "notification":
        return {
            "sent": True,
            "platform": config.get("platform", "generic"),
            "message": config.get("message", ""),
        }

    if node.type == "delay":
        seconds = config.get("seconds", config.get("minutes", 1) * 60)
        return {"delayed": True, "seconds": seconds}

    if node.type == "action":
        action = config.get("action", "unknown")
        return {"action": action, "executed": True, "config": config}

    return {"executed": True, "type": node.type, "config": config}


workflow_store = WorkflowStore()
