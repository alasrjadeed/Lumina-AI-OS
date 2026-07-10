from __future__ import annotations

import contextlib
import time
from dataclasses import dataclass, field

from core.agents.base import AgentResult, BaseAgent


@dataclass
class AgentMetadata:
    name: str
    capabilities: list[str] = field(default_factory=list)
    model: str = ""
    version: str = "1.0.0"
    status: str = "idle"
    last_used: float = 0.0
    task_count: int = 0
    error_count: int = 0
    avg_duration_ms: float = 0.0
    team: str = "default"


CAPABILITY_MAP: dict[str, list[str]] = {
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
}

CAPABILITY_ALIASES: dict[str, str] = {
    "write code": "programmer",
    "fix bug": "programmer",
    "debug": "programmer",
    "implement": "programmer",
    "build": "programmer",
    "refactor": "programmer",
    "review": "tester",
    "check": "tester",
    "create design": "designer",
    "make it look good": "designer",
    "deploy": "devops_engineer",
    "release": "devops_engineer",
    "secure": "security_auditor",
    "harden": "security_auditor",
    "backup": "database_engineer",
    "store": "database_engineer",
    "app": "mobile_developer",
    "advertise": "marketing_agent",
    "promote": "marketing_agent",
    "cost": "finance_agent",
    "write docs": "documentation_writer",
    "explain": "documentation_writer",
    "speak": "voice_assistant",
    "talk": "voice_assistant",
}


class AgentManager:
    """Manages agent lifecycle, routing, and health."""

    def __init__(self):
        self._agents: dict[str, BaseAgent] = {}
        self._metadata: dict[str, AgentMetadata] = {}

    def register(self, agent: BaseAgent, metadata: AgentMetadata | None = None) -> None:
        if agent.name in self._agents:
            raise ValueError(f"Agent {agent.name!r} already registered")
        key = agent.name.lower().replace(" ", "_")
        caps = CAPABILITY_MAP.get(key, [agent.name.lower()])
        self._agents[agent.name] = agent
        self._metadata[agent.name] = metadata or AgentMetadata(
            name=agent.name,
            capabilities=caps,
        )

    def unregister(self, name: str) -> None:
        self._agents.pop(name, None)
        self._metadata.pop(name, None)

    def get(self, name: str) -> BaseAgent | None:
        return self._agents.get(name)

    def get_metadata(self, name: str) -> AgentMetadata | None:
        return self._metadata.get(name)

    def list(self) -> list[str]:
        return sorted(self._agents.keys())

    def list_with_metadata(self) -> list[AgentMetadata]:
        return [self._metadata.get(n, AgentMetadata(name=n)) for n in self.list()]

    async def run(self, name: str, task: str, context: dict | None = None) -> AgentResult:
        agent = self.get(name)
        if not agent:
            return AgentResult(
                agent_name=name,
                status="error",
                output="",
                error=f"Unknown agent: {name}",
            )
        meta = self._metadata.get(name)
        if meta:
            meta.status = "running"
            meta.last_used = time.time()
        start = time.time()
        try:
            result = await agent.run(task, context)
            if meta:
                meta.task_count += 1
                if result.status == "error":
                    meta.error_count += 1
                dur = (time.time() - start) * 1000
                prev = meta.avg_duration_ms * (meta.task_count - 1)
                meta.avg_duration_ms = (
                    (prev + dur) / meta.task_count if meta.task_count > 1 else dur
                )
            return result
        finally:
            if meta:
                meta.status = "idle"

    async def route(self, task: str, preferred: str = "") -> AgentResult:
        if preferred and preferred in self._agents:
            return await self.run(preferred, task)
        best = self._find_best_agent(task)
        if best:
            return await self.run(best, task)
        return AgentResult(
            agent_name="none",
            status="error",
            output="",
            error="No suitable agent found for task",
        )

    def _find_best_agent(self, task: str) -> str | None:
        task_lower = task.lower()

        for alias, agent_name in CAPABILITY_ALIASES.items():
            if alias in task_lower and agent_name in self._agents:
                return agent_name

        agents_list = list(self._agents.keys())
        if not agents_list:
            return None

        scores: list[tuple[str, int]] = []
        for name in agents_list:
            meta = self._metadata.get(name)
            caps = meta.capabilities if meta else []
            score = sum(
                2 if f" {c} " in f" {task_lower} " else 1 if c in task_lower else 0 for c in caps
            )
            if meta:
                score -= meta.error_count
                if meta.avg_duration_ms > 0 and meta.task_count > 0:
                    score += max(0, 3 - int(meta.avg_duration_ms / 2000))
            scores.append((name, score))

        scores.sort(key=lambda x: (-x[1], x[0]))
        return scores[0][0] if scores[0][1] >= 0 else agents_list[0]

    def get_team_agents(self, team: str) -> list[str]:
        return sorted(name for name, meta in self._metadata.items() if meta.team == team)

    def health(self) -> dict[str, str]:
        result = {}
        for name, meta in self._metadata.items():
            if meta.error_count > 10 and meta.task_count > 0:
                ratio = meta.error_count / meta.task_count
                result[name] = "unhealthy" if ratio > 0.5 else "degraded"
            else:
                result[name] = "healthy"
        return result

    def register_many(self, agents: dict[str, BaseAgent]) -> None:
        for agent in agents.values():
            with contextlib.suppress(ValueError):
                self.register(agent)
