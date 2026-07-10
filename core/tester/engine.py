"""Self Tester — runs tests, detects errors, fixes them, repeats until success.

Like having a junior developer continuously testing and fixing code.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass

from core.log import log
from core.provider import engine


@dataclass
class TestResult:
    command: str
    success: bool
    output: str = ""
    error: str = ""
    duration_ms: float = 0.0
    attempt: int = 1


@dataclass
class FixAttempt:
    issue: str
    fix: str
    success: bool = False
    attempt: int = 1


class SelfTester:
    """Automated testing agent — runs code, finds errors, fixes them, retries.

    Usage:
        result = await tester.run("python -m pytest")
        result = await tester.run_with_fix("python -m pytest", "fix any errors")
        result = await tester.run_laravel("php artisan test")
    """

    def __init__(self, max_attempts: int = 5):
        self.max_attempts = max_attempts
        self._history: list[TestResult] = []

    async def run(self, command: str, timeout: int = 60, cwd: str = "") -> TestResult:
        """Run a command and return the result."""
        start = time.time()
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd or None,
            )
            tr = TestResult(
                command=command,
                success=result.returncode == 0,
                output=result.stdout[-2000:],
                error=result.stderr[-2000:],
                duration_ms=(time.time() - start) * 1000,
            )
        except subprocess.TimeoutExpired:
            tr = TestResult(
                command=command, success=False, error="TIMEOUT", duration_ms=timeout * 1000
            )
        except Exception as e:
            tr = TestResult(
                command=command,
                success=False,
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

        self._history.append(tr)
        log.info(
            "Tester: %s → %s (%.1fs)", command, "✅" if tr.success else "❌", tr.duration_ms / 1000
        )
        return tr

    async def run_with_fix(
        self, command: str, context: str = "", timeout: int = 60, cwd: str = ""
    ) -> dict:
        """Run a command, detect errors, use AI to fix, retry until success."""
        attempts = []
        for attempt in range(1, self.max_attempts + 1):
            log.info("Tester: Attempt %d/%d: %s", attempt, self.max_attempts, command)
            result = await self.run(command, timeout, cwd)
            attempts.append(
                {
                    "attempt": attempt,
                    "success": result.success,
                    "output": result.output[-500:],
                    "error": result.error[-500:],
                }
            )

            if result.success:
                log.info("Tester: ✅ Succeeded on attempt %d", attempt)
                return {"success": True, "attempts": attempt, "results": attempts}

            # AI fix
            fix = await self._generate_fix(result.error, result.output, command, context)
            if fix.get("command"):
                command = fix["command"]
                log.info("Tester: AI fixed command: %s", command)
                if fix.get("code"):
                    await self._apply_fix(fix["code"])

        log.info("Tester: ❌ Failed after %d attempts", self.max_attempts)
        return {"success": False, "attempts": self.max_attempts, "results": attempts}

    async def run_pytest(self, path: str = ".", flags: str = "-v") -> dict:
        """Run pytest with auto-fix loop."""
        return await self.run_with_fix(f"python -m pytest {path} {flags}")

    async def run_laravel(self, command: str = "php artisan test", cwd: str = "") -> dict:
        """Run Laravel tests with auto-fix loop."""
        return await self.run_with_fix(command, context="Laravel project", cwd=cwd)

    async def run_npm(self, script: str = "test", cwd: str = "") -> dict:
        """Run npm script with auto-fix loop."""
        return await self.run_with_fix(f"npm run {script}", cwd=cwd)

    async def run_typescript(self, cwd: str = "") -> dict:
        """Run TypeScript compiler check with auto-fix."""
        return await self.run_with_fix("npx tsc --noEmit", cwd=cwd)

    async def run_lint(self, path: str = ".") -> dict:
        """Run ruff linter with auto-fix."""
        return await self.run_with_fix(f"python -m ruff check --fix {path}")

    async def run_and_monitor(self, command: str, timeout: int = 120) -> dict:
        """Run a long-running command and monitor its output for errors."""
        import asyncio

        start = time.time()
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        output = stdout.decode() if stdout else ""
        errors = stderr.decode() if stderr else ""
        success = process.returncode == 0
        return {
            "success": success,
            "output": output[-2000:],
            "error": errors[-2000:],
            "duration_ms": (time.time() - start) * 1000,
        }

    async def _generate_fix(self, error: str, output: str, command: str, context: str) -> dict:
        """Use AI to generate a fix for the error."""
        prompt = f"""A command failed. Analyze the error and suggest a fix.

Command: {command}
Error: {error[:1000]}
Output: {output[:1000]}
Context: {context}

Return JSON:
{{"analysis": "what went wrong",
 "command": "corrected command to run",
 "code": "any code changes needed (or empty)"}}"""
        try:
            resp = await engine.chat([{"role": "user", "content": prompt}])
            text = resp.get("message", {}).get("content", "")
            import json
            import re

            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        return {"analysis": "Could not analyze", "command": command, "code": ""}

    async def _apply_fix(self, code: str) -> bool:
        """Apply a code fix. For now, just log it."""
        log.info("Tester: AI suggested code fix:\n%s", code[:500])
        return True

    def get_history(self, limit: int = 20) -> list[TestResult]:
        return self._history[-limit:]


tester = SelfTester()
