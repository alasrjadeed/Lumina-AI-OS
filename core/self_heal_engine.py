"""Self-Healing Code Engine — write → run → get errors → analyze → fix → retest → repeat."""

from __future__ import annotations

import os
import subprocess
import time
import traceback
from dataclasses import dataclass, field

from core.log import log


@dataclass
class HealStep:
    attempt: int
    action: str
    command: str = ""
    output: str = ""
    error: str = ""
    fix: str = ""
    status: str = "pending"
    duration_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "attempt": self.attempt, "action": self.action,
            "command": self.command, "output": self.output[:2000],
            "error": self.error[:2000], "fix": self.fix[:1000],
            "status": self.status, "duration_ms": self.duration_ms,
        }


@dataclass
class HealResult:
    task: str
    steps: list[HealStep] = field(default_factory=list)
    status: str = "pending"
    total_attempts: int = 0
    total_duration_ms: float = 0.0
    final_output: str = ""
    final_error: str = ""
    source_changed: list[str] = field(default_factory=list)
    tests_passed: bool = False

    def to_dict(self) -> dict:
        return {
            "task": self.task, "steps": [s.to_dict() for s in self.steps],
            "status": self.status, "total_attempts": self.total_attempts,
            "total_duration_ms": self.total_duration_ms,
            "final_output": self.final_output[:2000],
            "final_error": self.final_error[:2000],
            "source_changed": self.source_changed,
            "tests_passed": self.tests_passed,
        }


class SelfHealingEngine:
    """Automated write → run → fail → analyze → fix → retest loop."""

    def __init__(self, max_attempts: int = 5, project_dir: str = "."):
        self.max_attempts = max_attempts
        self.project_dir = os.path.abspath(project_dir)

    async def heal(self, task: str, test_command: str = "",
                   build_command: str = "", lint_command: str = "",
                   context: dict | None = None) -> HealResult:
        """Run the full self-healing loop."""
        import asyncio

        result = HealResult(task=task)
        start = time.time()

        try:
            from core.agents.runner import runner

            for attempt in range(1, self.max_attempts + 1):
                log.info("HealEngine: Attempt %d/%d for '%s'",
                         attempt, self.max_attempts, task[:60])

                # ── 1. Plan & Write ──
                step_plan = await self._step_plan(task, context, attempt)
                result.steps.append(step_plan)

                if step_plan.status == "failed":
                    continue

                # ── 2. Build (if needed) ──
                if build_command:
                    step_build = await self._step_build(build_command, attempt)
                    result.steps.append(step_build)
                    if step_build.status == "failed":
                        continue

                # ── 3. Lint (if needed) ──
                if lint_command:
                    step_lint = await self._step_lint(lint_command, attempt)
                    result.steps.append(step_lint)

                # ── 4. Test ──
                if test_command:
                    step_test = await self._step_test(test_command, attempt)
                    result.steps.append(step_test)

                    if step_test.status == "success":
                        result.tests_passed = True
                        result.status = "success"
                        break

                    error_output = step_test.error or step_test.output
                else:
                    error_output = "No test command provided"

                # ── 5. Analyze & Fix ──
                step_fix = await self._step_analyze_and_fix(
                    task, error_output, attempt, context,
                )
                result.steps.append(step_fix)

                if step_fix.status == "failed":
                    log.warning("HealEngine: Fix attempt %d failed", attempt)
                    continue

                # ── 6. Build again after fix ──
                if build_command:
                    step_build2 = await self._step_build(build_command, attempt, suffix="post-fix")
                    result.steps.append(step_build2)
                    if step_build2.status == "failed":
                        continue

                # ── 7. Test again after fix ──
                if test_command:
                    step_test2 = await self._step_test(test_command, attempt, suffix="post-fix")
                    result.steps.append(step_test2)
                    if step_test2.status == "success":
                        result.tests_passed = True
                        result.status = "success"
                        break

            if result.status != "success":
                result.status = "failed"
                result.final_error = "All self-healing attempts exhausted"

        except Exception as e:
            result.status = "failed"
            result.final_error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"

        result.total_attempts = len([s for s in result.steps if "plan" in s.action.lower() or "write" in s.action.lower()])
        result.total_duration_ms = (time.time() - start) * 1000

        return result

    async def _step_plan(self, task: str, context: dict | None,
                         attempt: int) -> HealStep:
        step = HealStep(attempt=attempt, action="plan_and_write")
        start = time.time()

        try:
            from core.agents.runner import runner
            prompt = task if attempt == 1 else (
                f"Previous attempt failed. Retry with a different approach: {task}"
            )
            run = await runner.run("programmer", prompt, context)
            step.output = run.output
            step.status = "success" if run.status == "success" else "failed"
            step.error = run.error
        except Exception as e:
            step.status = "failed"
            step.error = str(e)

        step.duration_ms = (time.time() - start) * 1000
        return step

    async def _step_build(self, command: str, attempt: int,
                          suffix: str = "") -> HealStep:
        step = HealStep(
            attempt=attempt,
            action=f"build_{suffix}" if suffix else "build",
            command=command,
        )
        start = time.time()

        try:
            proc = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                cwd=self.project_dir, timeout=120,
            )
            step.output = proc.stdout
            step.error = proc.stderr
            step.status = "success" if proc.returncode == 0 else "failed"
        except subprocess.TimeoutExpired:
            step.status = "failed"
            step.error = "Build timed out after 120s"
        except Exception as e:
            step.status = "failed"
            step.error = str(e)

        step.duration_ms = (time.time() - start) * 1000
        return step

    async def _step_lint(self, command: str, attempt: int) -> HealStep:
        step = HealStep(attempt=attempt, action="lint", command=command)
        start = time.time()

        try:
            proc = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                cwd=self.project_dir, timeout=60,
            )
            step.output = proc.stdout
            step.error = proc.stderr
        except Exception as e:
            step.error = str(e)

        step.duration_ms = (time.time() - start) * 1000
        step.status = "success"
        return step

    async def _step_test(self, command: str, attempt: int,
                         suffix: str = "") -> HealStep:
        step = HealStep(
            attempt=attempt,
            action=f"test_{suffix}" if suffix else "test",
            command=command,
        )
        start = time.time()

        try:
            proc = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                cwd=self.project_dir, timeout=120,
            )
            step.output = proc.stdout
            step.error = proc.stderr
            step.status = "success" if proc.returncode == 0 else "failed"
        except subprocess.TimeoutExpired:
            step.status = "failed"
            step.error = "Tests timed out after 120s"
        except Exception as e:
            step.status = "failed"
            step.error = str(e)

        step.duration_ms = (time.time() - start) * 1000
        return step

    async def _step_analyze_and_fix(
        self, task: str, error_output: str, attempt: int,
        context: dict | None,
    ) -> HealStep:
        step = HealStep(attempt=attempt, action="analyze_and_fix")
        start = time.time()

        try:
            from core.agents.runner import runner
            fix_prompt = (
                f"Original task: {task}\n\n"
                f"Tests FAILED with the following output:\n{error_output[:3000]}\n\n"
                f"Analyze the errors, identify the root cause, and fix the code. "
                f"Do NOT repeat the same approach. Consider edge cases."
            )
            run = await runner.run("debugger", fix_prompt, context)
            step.output = run.output
            if "fix" in run.output.lower() or "change" in run.output.lower():
                step.fix = run.output[:1000]
            step.status = "success" if run.status == "success" else "failed"
            step.error = run.error
        except Exception as e:
            step.status = "failed"
            step.error = str(e)

        step.duration_ms = (time.time() - start) * 1000
        return step


self_healing = SelfHealingEngine()
