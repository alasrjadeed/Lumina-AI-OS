from __future__ import annotations

import asyncio
import json
import re
import time
import traceback
from typing import Any

from core.agents.base import AgentResult, BaseAgent
from core.agents.manager import AgentManager
from core.log import log
from core.memory.engine import MemoryEngine
from core.provider import engine as ai_engine

SYSTEM_PROMPT = """You are Lumina CEO AI — the master orchestrator.

You coordinate specialized AI agents to accomplish tasks. Follow this lifecycle:
1. OBSERVE - Understand the user's request
2. THINK - Break down the task
3. PLAN - Create a step-by-step plan
4. ASSIGN - Delegate to appropriate agents
5. EXECUTE - Perform the work
6. VERIFY - Check results
7. REPORT - Summarize what was done

Available agents:
Core:
- SoftwareEngineer: Writes and debugs code
- WebDeveloper: Builds web applications
- BusinessManager: Handles business operations
- MarketingManager: SEO, social media, campaigns
- QAEngineer: Testing and quality
- DataAnalyst: Data analysis
- ResearchAnalyst: Research tasks

Specialized:
- LeadGenAI: Find leads, search businesses, enrich data
- QuotationAI: Create quotations and proposals
- EmailAssistantAI: Draft, reply, manage emails
- CallAssistantAI: VoIP, call scheduling, notes
- CustomerSuccessAI: Post-sale onboarding, retention
- DocumentationAI: Auto-generate documentation
- VoiceNarratorAI: Narration scripts, voiceover
- DesignerAI: Visual design, branding, UI

Content:
- MediaWriterAI: Blog posts, articles, copywriting
- MediaVideoAI: Video scripts, storyboards
- MediaPodcastAI: Podcast scripts, show notes
- ContentWriterAI: Multi-format content creation

Think step by step. Be thorough and practical."""


class TaskDecomposition:
    def __init__(
        self,
        summary: str,
        steps: list[dict[str, str]],
        dependencies: list[list[int]] | None = None,
    ):
        self.summary = summary
        self.steps = steps
        self.dependencies = dependencies or []


class OrchestrationResult:
    def __init__(
        self,
        status: str,
        output: str,
        error: str = "",
        steps: int = 0,
        duration_ms: float = 0.0,
    ):
        self.status = status
        self.output = output
        self.error = error
        self.steps = steps
        self.duration_ms = duration_ms

    def to_dict(self) -> dict[str, Any]:
        return vars(self)


class MultiAgentOrchestrator(BaseAgent):
    name = "CEO_AI"
    system_prompt = SYSTEM_PROMPT

    def __init__(
        self,
        agent_manager: AgentManager | None = None,
        memory: MemoryEngine | None = None,
    ):
        self.agent_manager = agent_manager or AgentManager()
        self.memory = memory

    async def run(self, task: str, context: dict | None = None) -> AgentResult:
        try:
            messages = [
                {"role": "system", "content": self.build_system_prompt(context)},
                {"role": "user", "content": task},
            ]
            result = await ai_engine.chat(messages)
            output = result["message"]["content"]
            return AgentResult(
                agent_name=self.name,
                status="success",
                output=output,
            )
        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                status="error",
                output="",
                error=f"{type(e).__name__}: {e}\n{traceback.format_exc()}",
            )

    async def orchestrate(
        self,
        task: str,
        parallel: bool = True,
    ) -> OrchestrationResult:
        start = time.time()

        if self.memory:
            context = await self.memory.recall_context(5)
            similar = await self.memory.recall_similar_episodes(task)
            lessons = await self.memory.recall_lessons()
        else:
            context = ""
            similar = []
            lessons = []

        decomposition = await self._decompose(task, context, similar, lessons)
        if not decomposition or not decomposition.steps:
            result = await self.agent_manager.route(task)
            return OrchestrationResult(
                status=result.status,
                output=result.output,
                error=result.error or "",
                steps=1,
                duration_ms=(time.time() - start) * 1000,
            )

        step_results: list[str] = []
        if parallel and not decomposition.dependencies:
            results = await asyncio.gather(
                *[self._execute_step(step, i) for i, step in enumerate(decomposition.steps)]
            )
            step_results.extend(r for r in results if r)
        else:
            for i, step in enumerate(decomposition.steps):
                result = await self._execute_step(step, i)
                if result:
                    step_results.append(result)

        synthesis = await self._synthesize(
            task,
            decomposition.summary,
            step_results,
            start,
        )

        if self.memory:
            await self.memory.record_episode(
                task=task,
                agent=self.name,
                action="orchestrate",
                result=synthesis,
                duration_ms=(time.time() - start) * 1000,
                success="error" not in synthesis.lower()[:100],
            )
            self.memory.save_all()

        return OrchestrationResult(
            status="success",
            output=synthesis,
            steps=len(decomposition.steps),
            duration_ms=(time.time() - start) * 1000,
        )

    async def _decompose(
        self,
        task: str,
        context: str = "",
        similar: list | None = None,
        lessons: list | None = None,
    ) -> TaskDecomposition | None:
        prompt = (
            "Break this task into steps. Return JSON with 'summary' and 'steps' "
            "(array of objects with 'agent', 'task', 'description')."
        )
        if context:
            prompt += f"\nContext: {context[:500]}"
        if similar:
            prompt += f"\nSimilar past tasks: {[s.task[:100] for s in similar[:2]]}"
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a task decomposition specialist. "
                    "Break complex tasks into steps assignable to AI agents."
                ),
            },
            {"role": "user", "content": f"{prompt}\n\nTask: {task}"},
        ]
        try:
            resp = await ai_engine.chat(messages)
            text = resp["message"]["content"]
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                data = json.loads(match.group())
                return TaskDecomposition(
                    summary=data.get("summary", task),
                    steps=data.get("steps", []),
                    dependencies=data.get("dependencies"),
                )
        except Exception:
            pass
        return None

    async def _execute_step(
        self,
        step: dict[str, str],
        index: int,
    ) -> str | None:
        agent_name = step.get("agent", "")
        step_task = step.get("task", step.get("description", ""))
        log.info("Step %d: %s -> %s", index + 1, agent_name or "CEO", step_task[:80])
        try:
            if agent_name and self.agent_manager.get(agent_name):
                result = await self.agent_manager.run(agent_name, step_task)
                if result.status == "success":
                    return result.output
                return f"[Step {index + 1} error: {result.error}]"
            else:
                messages = [
                    {
                        "role": "system",
                        "content": f"Execute this step: {step.get('description', '')}",
                    },
                    {"role": "user", "content": step_task},
                ]
                resp = await ai_engine.chat(messages)
                return resp["message"]["content"]
        except Exception as e:
            return f"[Step {index + 1} failed: {e}]"

    async def _synthesize(
        self,
        task: str,
        summary: str,
        step_results: list[str],
        start: float,
    ) -> str:
        duration = (time.time() - start) * 1000
        results_text = "\n\n".join(f"Step {i + 1}:\n{r[:1000]}" for i, r in enumerate(step_results))
        messages = [
            {
                "role": "system",
                "content": (
                    "Synthesize these step results into a coherent final response. "
                    "Include key findings and any actions taken."
                ),
            },
            {
                "role": "user",
                "content": f"Task: {task}\nPlan: {summary}\n\nResults:\n{results_text}",
            },
        ]
        try:
            resp = await ai_engine.chat(messages)
            synthesis = resp["message"]["content"]
            synthesis += (
                f"\n\n---\n*Orchestrated in {duration:.0f}ms across {len(step_results)} steps*"
            )
            return synthesis
        except Exception as e:
            return f"Completed {len(step_results)} steps. Synthesis error: {e}"


ceo = MultiAgentOrchestrator()
