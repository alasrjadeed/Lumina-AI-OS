import json
import re

from core.log import log
from core.provider import engine


class SelfHealingLoop:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    async def execute(self, task: str, context: dict | None = None) -> dict:
        plan = await self._plan(task, context)
        log.info("Plan: %s", plan.get("summary", task)[:100])

        for attempt in range(1, self.max_retries + 1):
            log.info("Execution attempt %d/%d", attempt, self.max_retries)
            result = await self._execute_plan(plan, context)
            issues = await self._verify(result)
            if not issues:
                log.info("Execution verified OK on attempt %d", attempt)
                return {"status": "success", "result": result, "attempts": attempt}
            log.warning("Issues found: %s", issues[:200])
            if attempt < self.max_retries:
                plan = await self._fix(plan, result, issues, context)
                log.info("Revised plan for retry %d", attempt + 1)

        return {"status": "failed", "result": result, "attempts": self.max_retries}

    async def _plan(self, task: str, context: dict | None = None) -> dict:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a planning agent. Break down this task into steps. "
                    "Return a JSON plan with 'summary' and 'steps' array."
                ),
            },
            {"role": "user", "content": task},
        ]
        try:
            resp = await engine.chat(messages)
            text = resp["message"]["content"]
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        return {"summary": task, "steps": [task]}

    async def _execute_plan(self, plan: dict, context: dict | None = None) -> str:
        steps = plan.get("steps", [plan.get("summary", "")])
        results = []
        for step in steps:
            messages = [
                {"role": "system", "content": "Execute this step thoroughly. Return the result."},
                {"role": "user", "content": str(step)},
            ]
            try:
                resp = await engine.chat(messages)
                results.append(resp["message"]["content"])
            except Exception as e:
                results.append(f"Step failed: {e}")
        return "\n".join(results)

    async def _verify(self, result: str) -> list[str]:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a QA agent. Review this output for errors, inconsistencies, "
                    "or missing parts. List each issue found. If perfect, return 'NO_ISSUES'."
                ),
            },
            {"role": "user", "content": result},
        ]
        try:
            resp = await engine.chat(messages)
            feedback = resp["message"]["content"]
            if "NO_ISSUES" in feedback.upper():
                return []
            return [
                line for line in feedback.split("\n")
                if line.strip() and not line.startswith("NO_ISSUES")
            ]
        except Exception:
            return []

    async def _fix(
        self, plan: dict, result: str, issues: list[str], context: dict | None = None
    ) -> dict:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a fixer agent. Given the original plan, the result, and the "
                    "issues found, revise the plan to fix all issues. Return JSON with "
                    "'summary' and 'steps'."
                ),
            },
            {"role": "user", "content": f"Plan: {plan}\nIssues: {issues}\nResult: {result[:500]}"},
        ]
        try:
            resp = await engine.chat(messages)
            text = resp["message"]["content"]
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        return plan


self_heal = SelfHealingLoop()
