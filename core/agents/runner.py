"""Advanced Agent Runner — persistent runs, context, batch execution, streaming."""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from datetime import datetime

from core.agents.base import BaseAgent
from core.agents.ceo import CEOAgent, OrchestrationRun
from core.agents.specialized import SPECIALIZED_AGENTS
from core.log import log

RUNS_DIR = os.path.expanduser("~/.lumina/agent_runs")

AGENT_CAPABILITIES: dict[str, list[str]] = {
    "ceo": ["orchestrate", "assign", "plan", "manage", "coordinate"],
    "planner": ["plan", "strategy", "roadmap", "milestone", "decomposition", "sprint", "timeline"],
    "programmer": [
        "code",
        "program",
        "develop",
        "software",
        "backend",
        "frontend",
        "api",
        "fullstack",
        "python",
        "typescript",
        "javascript",
        "rust",
        "golang",
        "algorithm",
    ],
    "tester": [
        "test",
        "qa",
        "quality",
        "bug",
        "validation",
        "verify",
        "assert",
        "pytest",
        "coverage",
    ],
    "debugger": [
        "debug",
        "trace",
        "stack",
        "root cause",
        "fix bug",
        "log analysis",
        "breakpoint",
        "crash",
        "reproduce",
        "bisect",
    ],
    "graphic_designer": [
        "graphic",
        "logo",
        "banner",
        "brand identity",
        "flyer",
        "brochure",
        "infographic",
        "mockup",
        "presentation",
    ],
    "executive_planner": [
        "strategy",
        "executive",
        "roadmap",
        "portfolio",
        "initiative",
        "go-to-market",
        "architecture decision",
        "budget",
    ],
    "project_manager": [
        "project",
        "sprint",
        "agile",
        "backlog",
        "milestone",
        "deliverable",
        "stakeholder",
        "retrospective",
    ],
    "research_analyst": [
        "research",
        "market analysis",
        "competitive",
        "benchmark",
        "literature review",
        "vendor evaluation",
        "trend",
    ],
    "data_analyst": [
        "data",
        "statistics",
        "hypothesis",
        "forecast",
        "dashboard",
        "cohort",
        "segmentation",
        "ab test",
        "kpi",
    ],
    "content_writer": [
        "content",
        "blog",
        "article",
        "newsletter",
        "copy",
        "social post",
        "script",
        "case study",
        "press release",
    ],
    "designer": [
        "design",
        "ui",
        "ux",
        "visual",
        "layout",
        "css",
        "tailwind",
        "figma",
        "brand",
        "typography",
        "color",
        "accessible",
        "responsive",
    ],
    "browser_operator": [
        "browser",
        "web",
        "scrape",
        "automation",
        "navigate",
        "form",
        "screenshot",
    ],
    "devops_engineer": [
        "devops",
        "deploy",
        "ci/cd",
        "docker",
        "kubernetes",
        "infrastructure",
        "terraform",
        "monitoring",
        "pipeline",
    ],
    "security_auditor": [
        "security",
        "audit",
        "vulnerability",
        "owasp",
        "compliance",
        "gdpr",
        "encrypt",
        "authentication",
        "penetration",
    ],
    "database_engineer": [
        "database",
        "sql",
        "schema",
        "query",
        "migration",
        "postgresql",
        "mongodb",
        "redis",
        "data model",
        "index",
    ],
    "mobile_developer": ["mobile", "flutter", "react native", "android", "ios", "dart", "kotlin"],
    "marketing_agent": [
        "marketing",
        "seo",
        "campaign",
        "social media",
        "content",
        "growth",
        "brand",
        "advertising",
        "analytics",
    ],
    "finance_agent": [
        "finance",
        "budget",
        "forecast",
        "revenue",
        "cost",
        "pricing",
        "invoice",
        "financial",
        "roi",
    ],
    "documentation_writer": [
        "document",
        "docs",
        "readme",
        "guide",
        "tutorial",
        "api reference",
        "changelog",
        "wiki",
        "manual",
    ],
    "voice_assistant": [
        "voice",
        "speech",
        "tts",
        "stt",
        "audio",
        "narration",
        "conversation",
        "vui",
        "dialog",
    ],
    "sales_agent": [
        "sales",
        "pipeline",
        "closing",
        "prospecting",
        "negotiation",
        "crm",
        "quota",
        "forecasting",
    ],
    "customer_support_agent": [
        "support",
        "ticket",
        "helpdesk",
        "customer",
        "faq",
        "troubleshooting",
        "escalation",
        "refund",
    ],
    "email_manager": [
        "email",
        "inbox",
        "triage",
        "categorize",
        "draft",
        "reply",
        "newsletter",
        "follow-up",
    ],
    "accountant": [
        "accounting",
        "bookkeeping",
        "invoice",
        "expense",
        "tax",
        "ledger",
        "reconciliation",
        "cashflow",
    ],
    "personal_assistant": [
        "assistant",
        "calendar",
        "schedule",
        "meeting",
        "travel",
        "reminder",
        "agenda",
        "itinerary",
    ],
    "social_media_manager": [
        "social",
        "post",
        "tweet",
        "instagram",
        "linkedin",
        "facebook",
        "tiktok",
        "engagement",
        "content calendar",
    ],
    "proposal_writer": ["proposal", "rfp", "rfq", "bid", "sow", "quote", "scope", "pricing"],
    "security_monitor": [
        "monitor",
        "ids",
        "ips",
        "log",
        "alert",
        "incident",
        "threat",
        "vulnerability scan",
    ],
}

AGENT_METADATA: dict[str, dict] = {
    "ceo": {
        "name": "CEO AI",
        "category": "orchestrator",
        "description": "Orchestrates multi-agent workflows across all specialists",
        "icon": "Crown",
        "capabilities": AGENT_CAPABILITIES["ceo"],
        "team": "leadership",
    },
    "planner": {
        "name": "Planner",
        "category": "specialist",
        "description": "Strategic planning, task decomposition, milestones",
        "icon": "ClipboardList",
        "capabilities": AGENT_CAPABILITIES["planner"],
        "team": "development",
    },
    "programmer": {
        "name": "Programmer",
        "category": "specialist",
        "description": "Full-stack software development and coding",
        "icon": "Code",
        "capabilities": AGENT_CAPABILITIES["programmer"],
        "team": "development",
    },
    "tester": {
        "name": "Tester",
        "category": "specialist",
        "description": "Quality assurance, testing, and bug detection",
        "icon": "Bug",
        "capabilities": AGENT_CAPABILITIES["tester"],
        "team": "quality",
    },
    "debugger": {
        "name": "Debugger",
        "category": "specialist",
        "description": "Intelligent debugging — read source, reproduce, trace, fix, verify",
        "icon": "Bug",
        "capabilities": AGENT_CAPABILITIES["debugger"],
        "team": "quality",
    },
    "graphic_designer": {
        "name": "Graphic Designer",
        "category": "specialist",
        "description": "Visual design — logos, banners, brand assets, social posts",
        "icon": "Image",
        "capabilities": AGENT_CAPABILITIES["graphic_designer"],
        "team": "design",
    },
    "executive_planner": {
        "name": "Executive Planner",
        "category": "specialist",
        "description": "Senior strategic planning, roadmaps, portfolio management",
        "icon": "Target",
        "capabilities": AGENT_CAPABILITIES["executive_planner"],
        "team": "leadership",
    },
    "project_manager": {
        "name": "Project Manager",
        "category": "specialist",
        "description": "Project coordination, sprints, milestones, stakeholder updates",
        "icon": "Kanban",
        "capabilities": AGENT_CAPABILITIES["project_manager"],
        "team": "leadership",
    },
    "research_analyst": {
        "name": "Research Analyst",
        "category": "specialist",
        "description": "Deep research, market analysis, competitive intelligence",
        "icon": "Search",
        "capabilities": AGENT_CAPABILITIES["research_analyst"],
        "team": "business",
    },
    "data_analyst": {
        "name": "Data Analyst",
        "category": "specialist",
        "description": "Data analysis, statistics, dashboards, forecasting",
        "icon": "PieChart",
        "capabilities": AGENT_CAPABILITIES["data_analyst"],
        "team": "business",
    },
    "content_writer": {
        "name": "Content Writer",
        "category": "specialist",
        "description": "Professional content — blogs, social, scripts, newsletters, copy",
        "icon": "PenLine",
        "capabilities": AGENT_CAPABILITIES["content_writer"],
        "team": "content",
    },
    "designer": {
        "name": "Designer",
        "category": "specialist",
        "description": "UI/UX design, design systems, visual branding",
        "icon": "Palette",
        "capabilities": AGENT_CAPABILITIES["designer"],
        "team": "design",
    },
    "browser_operator": {
        "name": "Browser Operator",
        "category": "specialist",
        "description": "Web automation, scraping, form filling",
        "icon": "Globe",
        "capabilities": AGENT_CAPABILITIES["browser_operator"],
        "team": "automation",
    },
    "devops_engineer": {
        "name": "DevOps Engineer",
        "category": "specialist",
        "description": "CI/CD, Docker, K8s, cloud infrastructure",
        "icon": "Container",
        "capabilities": AGENT_CAPABILITIES["devops_engineer"],
        "team": "infrastructure",
    },
    "security_auditor": {
        "name": "Security Auditor",
        "category": "specialist",
        "description": "Vulnerability assessment, compliance, OWASP",
        "icon": "Shield",
        "capabilities": AGENT_CAPABILITIES["security_auditor"],
        "team": "security",
    },
    "database_engineer": {
        "name": "Database Engineer",
        "category": "specialist",
        "description": "Schema design, queries, migrations, optimization",
        "icon": "Database",
        "capabilities": AGENT_CAPABILITIES["database_engineer"],
        "team": "infrastructure",
    },
    "mobile_developer": {
        "name": "Mobile Developer",
        "category": "specialist",
        "description": "Flutter, React Native, native mobile apps",
        "icon": "Smartphone",
        "capabilities": AGENT_CAPABILITIES["mobile_developer"],
        "team": "development",
    },
    "marketing_agent": {
        "name": "Marketing Agent",
        "category": "specialist",
        "description": "Campaigns, SEO, content, growth strategy",
        "icon": "Megaphone",
        "capabilities": AGENT_CAPABILITIES["marketing_agent"],
        "team": "business",
    },
    "finance_agent": {
        "name": "Finance Agent",
        "category": "specialist",
        "description": "Budgeting, forecasting, financial analysis",
        "icon": "BarChart3",
        "capabilities": AGENT_CAPABILITIES["finance_agent"],
        "team": "business",
    },
    "documentation_writer": {
        "name": "Documentation Writer",
        "category": "specialist",
        "description": "API docs, guides, ADRs, READMEs",
        "icon": "FileText",
        "capabilities": AGENT_CAPABILITIES["documentation_writer"],
        "team": "content",
    },
    "voice_assistant": {
        "name": "Voice Assistant",
        "category": "specialist",
        "description": "TTS/STT, voice UI, conversation design",
        "icon": "Headphones",
        "capabilities": AGENT_CAPABILITIES["voice_assistant"],
        "team": "content",
    },
    "sales_agent": {
        "name": "Sales Agent",
        "category": "specialist",
        "description": "Sales strategy, pipeline management, proposals, closing",
        "icon": "TrendingUp",
        "capabilities": AGENT_CAPABILITIES["sales_agent"],
        "team": "business",
    },
    "customer_support_agent": {
        "name": "Customer Support",
        "category": "specialist",
        "description": "Ticket triage, helpdesk, troubleshooting, FAQs",
        "icon": "HelpCircle",
        "capabilities": AGENT_CAPABILITIES["customer_support_agent"],
        "team": "support",
    },
    "email_manager": {
        "name": "Email Manager",
        "category": "specialist",
        "description": "Inbox triage, smart categorization, draft replies",
        "icon": "AtSign",
        "capabilities": AGENT_CAPABILITIES["email_manager"],
        "team": "communication",
    },
    "accountant": {
        "name": "Accountant",
        "category": "specialist",
        "description": "Bookkeeping, invoices, tax prep, cash flow",
        "icon": "Calculator",
        "capabilities": AGENT_CAPABILITIES["accountant"],
        "team": "business",
    },
    "personal_assistant": {
        "name": "Personal Assistant",
        "category": "specialist",
        "description": "Calendar, scheduling, meetings, travel planning",
        "icon": "Calendar",
        "capabilities": AGENT_CAPABILITIES["personal_assistant"],
        "team": "support",
    },
    "social_media_manager": {
        "name": "Social Media Manager",
        "category": "specialist",
        "description": "Content calendars, posting, engagement, analytics",
        "icon": "Share2",
        "capabilities": AGENT_CAPABILITIES["social_media_manager"],
        "team": "marketing",
    },
    "proposal_writer": {
        "name": "Proposal Writer",
        "category": "specialist",
        "description": "RFPs, business proposals, SOWs, branded PDFs",
        "icon": "PenLine",
        "capabilities": AGENT_CAPABILITIES["proposal_writer"],
        "team": "business",
    },
    "security_monitor": {
        "name": "Security Monitor",
        "category": "specialist",
        "description": "Real-time security monitoring, alerts, incident response",
        "icon": "Eye",
        "capabilities": AGENT_CAPABILITIES["security_monitor"],
        "team": "security",
    },
}

ALL_CATEGORIES = {
    "orchestrator": ["ceo"],
    "specialist": [k for k in AGENT_METADATA if k != "ceo"],
}

ALL_AGENTS: dict[str, BaseAgent] = {}
ALL_AGENTS["ceo"] = CEOAgent()
ALL_AGENTS.update(SPECIALIZED_AGENTS)

for agent_id, agent in ALL_AGENTS.items():
    meta = AGENT_METADATA.get(agent_id, {})
    if not agent.system_prompt or agent.system_prompt == "You are a helpful AI assistant.":
        agent.system_prompt = (
            f"You are Lumina {meta.get('name', agent.name)} AI Agent.\n"
            f"You are an expert in {meta.get('description', 'your field')}.\n"
            f"Complete the task thoroughly and professionally.\n"
            f"Provide detailed, actionable output."
        )


class AgentRun:
    def __init__(self, run_id: str, agent_id: str, task: str, context: dict | None = None):
        self.run_id = run_id
        self.agent_id = agent_id
        self.agent_name = AGENT_METADATA.get(agent_id, {}).get("name", agent_id)
        self.task = task
        self.context = context or {}
        self.status = "pending"
        self.output = ""
        self.error = ""
        self.started_at = datetime.now().isoformat()
        self.completed_at = ""
        self.duration_ms = 0
        self.model = ""
        self.thinking: list[dict] = []

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "task": self.task,
            "context": self.context,
            "status": self.status,
            "output": self.output,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "model": self.model,
            "thinking": self.thinking[-20:],
        }

    @classmethod
    def from_dict(cls, d: dict) -> AgentRun:
        r = cls(d["run_id"], d["agent_id"], d["task"], d.get("context", {}))
        r.status = d.get("status", "pending")
        r.output = d.get("output", "")
        r.error = d.get("error", "")
        r.started_at = d.get("started_at", r.started_at)
        r.completed_at = d.get("completed_at", "")
        r.duration_ms = d.get("duration_ms", 0)
        r.model = d.get("model", "")
        r.thinking = d.get("thinking", [])
        return r


class AgentRunner:
    def __init__(self):
        self._runs: list[AgentRun] = []
        self._orch_runs: list[OrchestrationRun] = []
        self._load()

    def _runs_path(self) -> str:
        os.makedirs(RUNS_DIR, exist_ok=True)
        return os.path.join(RUNS_DIR, "runs.json")

    def _orch_path(self) -> str:
        os.makedirs(RUNS_DIR, exist_ok=True)
        return os.path.join(RUNS_DIR, "orchestrations.json")

    def _load(self):
        path = self._runs_path()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                self._runs = [AgentRun.from_dict(d) for d in data[-200:]]
            except Exception as e:
                log.error("Failed to load agent runs: %s", e)
        orch_path = self._orch_path()
        if os.path.exists(orch_path):
            try:
                with open(orch_path) as f:
                    orch_data = json.load(f)
                for d in orch_data[-50:]:
                    run = OrchestrationRun(d.get("run_id", ""), d.get("task", ""))
                    run.status = d.get("status", "unknown")
                    run.output = d.get("output", "")
                    run.error = d.get("error", "")
                    run.duration_ms = d.get("duration_ms", 0)
                    run.started_at = d.get("started_at", 0)
                    run.completed_at = d.get("completed_at", 0)
                    for pd in d.get("phases", []):
                        from core.agents.ceo import TaskStep

                        step = TaskStep(
                            id=pd.get("id", ""),
                            agent=pd.get("agent", ""),
                            task=pd.get("task", ""),
                            description=pd.get("description", ""),
                            depends_on=pd.get("depends_on", []),
                        )
                        step.status = pd.get("status", "pending")
                        step.result = pd.get("result")
                        step.error = pd.get("error")
                        step.duration_ms = pd.get("duration_ms", 0)
                        run.phases.append(step)
                    self._orch_runs.append(run)
            except Exception as e:
                log.error("Failed to load orchestrations: %s", e)

    def _save(self):
        try:
            data = [r.to_dict() for r in self._runs[-200:]]
            with open(self._runs_path(), "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            log.error("Failed to save runs: %s", e)
        try:
            data = [r.to_dict() for r in self._orch_runs[-50:]]
            with open(self._orch_path(), "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            log.error("Failed to save orchestrations: %s", e)

    def get_agent(self, agent_id: str) -> BaseAgent | None:
        return ALL_AGENTS.get(agent_id)

    def get_metadata(self, agent_id: str) -> dict | None:
        return AGENT_METADATA.get(agent_id)

    def list_agents(self) -> list[dict]:
        result = []
        for agent_id, meta in AGENT_METADATA.items():
            result.append({**meta, "id": agent_id})
        return result

    def get_categories(self) -> dict[str, list[str]]:
        return ALL_CATEGORIES

    async def run(
        self, agent_id: str, task: str, context: dict | None = None, model: str = ""
    ) -> AgentRun:
        agent = self.get_agent(agent_id)
        run = AgentRun(
            run_id=uuid.uuid4().hex[:12],
            agent_id=agent_id,
            task=task,
            context=context or {},
        )
        run.status = "running"
        run.model = model
        self._runs.insert(0, run)
        start = time.time()
        try:
            if not agent:
                raise ValueError(f"Unknown agent: {agent_id}")
            if isinstance(agent, CEOAgent):
                orch_run = await agent.orchestrate(task, context)
                run.output = orch_run.output
                run.error = orch_run.error or ""
                run.status = "success" if orch_run.status == "success" else "failed"
            else:
                result = await agent.run(task, context)
                run.output = result.output
                run.error = result.error or ""
                run.status = "success" if result.status == "success" else "failed"
        except Exception as e:
            run.status = "failed"
            run.error = f"{type(e).__name__}: {e}"
        run.duration_ms = int((time.time() - start) * 1000)
        run.completed_at = datetime.now().isoformat()
        self._save()
        return run

    async def orchestrate(self, task: str, context: dict | None = None) -> OrchestrationRun:
        ceo_agent = self.get_agent("ceo")
        if not isinstance(ceo_agent, CEOAgent):
            raise RuntimeError("CEO agent not available")
        run = await ceo_agent.orchestrate(task, context)
        self._orch_runs.insert(0, run)
        self._save()
        return run

    async def run_batch(self, tasks: list[dict]) -> list[AgentRun]:
        coros = [
            self.run(
                t.get("agent_id", ""),
                t.get("task", ""),
                t.get("context"),
                t.get("model", ""),
            )
            for t in tasks
        ]
        results = await asyncio.gather(*coros, return_exceptions=True)
        final = []
        for r in results:
            if isinstance(r, AgentRun):
                final.append(r)
            else:
                run = AgentRun("error", "", "")
                run.status = "failed"
                run.error = str(r)
                final.append(run)
        return final

    def get_history(self, agent_id: str | None = None, limit: int = 50) -> list[AgentRun]:
        if agent_id:
            filtered = [r for r in self._runs if r.agent_id == agent_id]
        else:
            filtered = self._runs.copy()
        filtered.sort(key=lambda r: r.started_at, reverse=True)
        return filtered[:limit]

    def get_run(self, run_id: str) -> AgentRun | None:
        for r in self._runs:
            if r.run_id == run_id:
                return r
        return None

    def get_orch_history(self, limit: int = 20) -> list[OrchestrationRun]:
        return self._orch_runs[:limit]

    def get_orch_run(self, run_id: str) -> OrchestrationRun | None:
        for r in self._orch_runs:
            if r.run_id == run_id:
                return r
        return None


runner = AgentRunner()
