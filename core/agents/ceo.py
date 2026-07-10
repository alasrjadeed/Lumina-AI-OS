from __future__ import annotations

import json
import re
import time
import traceback

from core.agents.base import AgentResult, BaseAgent
from core.agents.manager import AgentManager
from core.log import log
from core.provider import engine as ai_engine

CEO_SYSTEM_PROMPT = """You are Lumina CEO AI — the master orchestrator of a multi-agent system.

Your 27 specialists:
Leadership:
- Executive Planner: senior strategy, roadmaps, portfolio, go-to-market
- Project Manager: sprints, milestones, coordination, stakeholder updates
- Planner: strategic planning, task decomposition, milestones

Development:
- Programmer: full-stack software development, code writing
- Tester: QA, unit/integration/e2e testing, bug detection
- Debugger: root cause analysis, trace→fix→verify→report
- Database Engineer: schema design, queries, migrations, optimization
- DevOps Engineer: CI/CD, Docker, K8s, cloud infrastructure
- Mobile Developer: Flutter, React Native, native mobile apps

Design:
- Designer: UI/UX, visual design, design systems, CSS
- Graphic Designer: logos, banners, social posts, brand assets, presentations

Business:
- Sales Agent: pipeline management, proposals, closing
- Marketing Agent: campaigns, SEO, content, growth strategy
- Finance Agent: budgeting, forecasting, financial analysis
- Accountant: bookkeeping, invoices, tax prep, cash flow
- Proposal Writer: RFPs, business proposals, SOWs
- Social Media Manager: content calendars, posting, analytics
- Research Analyst: market research, competitive analysis, benchmarks
- Data Analyst: statistics, dashboards, forecasting, AB tests

Operations:
- Browser Operator: web automation, scraping, form filling
- Security Auditor: vulnerability assessment, compliance, OWASP
- Security Monitor: real-time monitoring, alerts, incidents
- Email Manager: inbox triage, smart categories, drafts
- Customer Support: ticket triage, helpdesk, troubleshooting
- Personal Assistant: calendar, scheduling, meetings

Content & Voice:
- Documentation Writer: API docs, guides, ADRs, READMEs
- Voice Assistant: TTS/STT, voice UI, conversation design

Your workflow:
1. UNDERSTAND — Detect language, parse intent, recall past knowledge
2. PLAN — Break into phases with dependencies and assign specialists
3. APPROVE — Check if action needs human approval (financial, deploy, external comms)
4. DELEGATE — Execute each phase by calling the right specialist
5. VERIFY — Review results for quality and correctness
6. ITERATE — If verification fails, reassign for fixes
7. REPORT — Synthesize everything into a clear final response
8. LEARN — Store what worked and what didn't for future improvement

MULTI-LANGUAGE: Always detect the user's language and respond in that language.
APPROVAL GATES: For sensitive actions (payments, deployment, contract signing), \
request human approval.

Always think step by step. Be decisive, clear, and proactive."""


class TaskStep:
    def __init__(
        self, id: str, agent: str, task: str, description: str, depends_on: list[str] | None = None
    ):
        self.id = id
        self.agent = agent
        self.task = task
        self.description = description
        self.depends_on = depends_on or []
        self.status = "pending"
        self.result: str | None = None
        self.error: str | None = None
        self.duration_ms = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent": self.agent,
            "task": self.task,
            "description": self.description,
            "depends_on": self.depends_on,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


class OrchestrationRun:
    def __init__(self, run_id: str, task: str):
        self.run_id = run_id
        self.task = task
        self.phases: list[TaskStep] = []
        self.status = "pending"
        self.output = ""
        self.error = ""
        self.started_at = time.time()
        self.completed_at = 0.0
        self.duration_ms = 0.0

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "task": self.task,
            "phases": [s.to_dict() for s in self.phases],
            "status": self.status,
            "output": self.output,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
        }


class CEOAgent(BaseAgent):
    name = "CEO AI"
    system_prompt = CEO_SYSTEM_PROMPT

    def __init__(self, agent_manager: AgentManager | None = None):
        super().__init__(name=self.name, system_prompt=self.system_prompt)
        self.agent_manager = agent_manager or _init_default_manager()

    async def orchestrate(self, task: str, context: dict | None = None) -> OrchestrationRun:
        import uuid

        run = OrchestrationRun(run_id=uuid.uuid4().hex[:12], task=task)
        run.status = "running"
        start = time.time()

        try:
            log.info("CEO: Orchestrating task: %s", task[:80])
            steps = await self._decompose(task, context or {})

            if not steps:
                result = await self.run(task, context)
                run.output = result.output
                run.status = "success" if result.status == "success" else "failed"
                run.error = result.error or ""
                run.duration_ms = (time.time() - start) * 1000
                run.completed_at = time.time()
                return run

            run.phases = steps

            for phase in run.phases:
                if run.status == "cancelled":
                    break

                deps_met = all(
                    s.status == "success" for s in run.phases if s.id in phase.depends_on
                )
                if not deps_met:
                    phase.status = "skipped"
                    phase.error = "Dependencies not met"
                    continue

                phase.status = "running"
                phase_start = time.time()
                try:
                    result = await self._delegate(phase.agent, phase.task)
                    phase.duration_ms = (time.time() - phase_start) * 1000
                    if result.status == "success":
                        phase.status = "success"
                        phase.result = result.output
                    else:
                        phase.status = "failed"
                        phase.error = result.error or "Unknown error"
                except Exception as e:
                    phase.duration_ms = (time.time() - phase_start) * 1000
                    phase.status = "failed"
                    phase.error = f"{type(e).__name__}: {e}"

            failed_phases = [s for s in run.phases if s.status == "failed"]
            if failed_phases:
                run.status = (
                    "partial" if any(s.status == "success" for s in run.phases) else "failed"
                )
                failed_names = ", ".join(s.agent for s in failed_phases)
                run.error = f"{len(failed_phases)} phase(s) failed: {failed_names}"
            else:
                run.status = "success"

            run.output = await self._synthesize(task, run.phases, start)
            if not run.output:
                ok_count = len([s for s in run.phases if s.status == "success"])
                run.output = f"Completed {ok_count}/{len(run.phases)} phases."

        except Exception as e:
            run.status = "failed"
            run.error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"

        run.duration_ms = (time.time() - start) * 1000
        run.completed_at = time.time()
        return run

    async def _decompose(
        self,
        task: str,
        context: dict,
    ) -> list[TaskStep] | None:
        agents_desc = (
            "\n".join(
                f"- {name}: {meta.capabilities}"
                for name, meta in self.agent_manager._metadata.items()
            )
            if hasattr(self.agent_manager, "_metadata")
            else ""
        )

        prompt = (
            f"Break this task into a sequence of phases, each assigned to one specialist agent.\n\n"
            f"Available agents:\n{agents_desc}\n\n"
            f"Return valid JSON ONLY — an object with a 'phases' array. "
            f"Each phase has: id (short string), agent (agent name), task (detailed instruction), "
            f"description (one-line summary), depends_on (list of phase IDs that must "
            f"complete first, or []).\n\n"
            f"Example:\n"
            r'{{"phases": [{{"id":"p1","agent":"Planner","task":"Create plan for...",'
            r'"description":"Plan the work","depends_on":[]}}]}}'
        )

        messages = [
            {
                "role": "system",
                "content": "You are a precise task decomposition engine. Output ONLY valid JSON.",
            },
            {"role": "user", "content": f"{prompt}\n\nTask: {task}"},
        ]

        try:
            resp = await ai_engine.chat(messages)
            text = resp["message"]["content"]
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                data = json.loads(match.group())
                return [
                    TaskStep(
                        id=s["id"],
                        agent=s["agent"],
                        task=s["task"],
                        description=s.get("description", s["task"][:80]),
                        depends_on=s.get("depends_on", []),
                    )
                    for s in data.get("phases", [])
                ]
        except Exception as e:
            log.error("CEO: Decomposition failed: %s", e)
        return None

    async def _delegate(self, agent_name: str, task: str) -> AgentResult:
        agent = self.agent_manager.get(agent_name)
        if agent:
            log.info("CEO: Delegating to %s: %s", agent_name, task[:60])
            return await self.agent_manager.run(agent_name, task)
        messages = [
            {
                "role": "system",
                "content": f"You are acting as {agent_name}. Complete the following task.",
            },
            {"role": "user", "content": task},
        ]
        try:
            resp = await ai_engine.chat(messages)
            return AgentResult(
                agent_name=agent_name,
                status="success",
                output=resp["message"]["content"],
            )
        except Exception as e:
            return AgentResult(
                agent_name=agent_name,
                status="error",
                output="",
                error=str(e),
            )

    async def _synthesize(
        self,
        task: str,
        phases: list[TaskStep],
        start: float,
    ) -> str:
        duration = (time.time() - start) * 1000
        completed = [s for s in phases if s.status == "success"]
        failed = [s for s in phases if s.status == "failed"]

        if not completed:
            return ""

        results_text = "\n\n".join(
            f"Phase {i + 1} ({s.agent}):\n{s.result[:2000] if s.result else '(no output)'}"
            for i, s in enumerate(completed)
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "Synthesize these phase results into a clear final response. "
                    "Highlight key deliverables, decisions, and next steps. "
                    "If any phases failed, note what went wrong."
                ),
            },
            {
                "role": "user",
                "content": f"Original task: {task}\n\nResults:\n{results_text}",
            },
        ]

        try:
            resp = await ai_engine.chat(messages)
            report = resp["message"]["content"]
            report += (
                f"\n\n---\n*Orchestrated in {duration:.0f}ms "
                f"across {len(phases)} phases "
                f"({len(completed)} succeeded, {len(failed)} failed)*"
            )
            return report
        except Exception:
            return f"Completed {len(completed)} phases. ({duration:.0f}ms)"


def _init_default_manager() -> AgentManager:
    from core.agents.specialized import SPECIALIZED_AGENTS

    mgr = AgentManager()
    for agent in SPECIALIZED_AGENTS.values():
        mgr.register(agent)
    return mgr


ceo = CEOAgent()
