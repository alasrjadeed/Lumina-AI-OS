"""Lumina Core AI — the unified brain: understand → plan → execute → heal → learn → report."""

from __future__ import annotations

import time
import traceback
from typing import Any

from core.agents.approval import ApprovalLevel, approval_gate
from core.agents.ceo import CEOAgent
from core.agents.employee import LuminaEmployee
from core.agents.languages import language_engine
from core.agents.learning import learning_engine
from core.agents.routine import autonomous_routine
from core.audit import AuditAction, audit_trail
from core.analytics import analytics
from core.vault.memory import business_memory
from core.log import log


class CoreAI:
    """Lumina's unified brain — one call handles everything from language detection
    to execution, self-healing, learning, and reporting."""

    def __init__(self):
        self.employee = LuminaEmployee()
        self.working_language = "en"

    async def think(self, input_text: str, context: dict | None = None,
                    auto_heal: bool = True, max_retries: int = 3) -> dict:
        """The main entry point for ALL Lumina requests — text, voice, or API.

        Full pipeline:
        Understand → Plan → Assign → Execute → Heal → Verify → Learn → Report
        """
        start_time = time.time()
        task_id = f"core_{int(start_time)}"

        # ── 1. UNDERSTAND ──
        detected_lang = language_engine.detect(input_text)
        lang_name = language_engine.get_name(detected_lang)
        log.info("CoreAI: [%s] Language: %s (%s)", task_id, lang_name, detected_lang)

        domain = self._classify_domain(input_text)

        # ── 2. RECALL ──
        prior_knowledge = await learning_engine.get_knowledge_for_task(input_text)
        similar_experiences = await learning_engine.recall_similar(input_text, limit=3)

        # ── 3. PLAN & EXECUTE ──
        full_context = context or {}
        if detected_lang != self.working_language:
            full_context["language_prompt"] = language_engine.build_multilingual_prompt(input_text)
            full_context["detected_language"] = detected_lang
        if prior_knowledge:
            full_context["prior_knowledge"] = prior_knowledge

        vault_context = business_memory.build_context_prompt()
        if vault_context:
            full_context["business_memory"] = vault_context

        result = await self.employee.handle_request(input_text, full_context)
        execution_success = result.get("status") == "success"

        # ── 4. SELF-HEAL (if enabled) ──
        if auto_heal and not execution_success and max_retries > 0:
            log.info("CoreAI: [%s] Self-healing — attempt 1/%d", task_id, max_retries)
            result = await self._self_heal(
                input_text, result, full_context, max_retries, start_time,
            )

        # ── 5. VERIFY ──
        verification = await self._verify_result(input_text, result)

        # ── 6. LEARN ──
        duration_ms = (time.time() - start_time) * 1000
        final_success = result.get("status") == "success"

        if verification.get("issues"):
            await learning_engine.extract_lesson(
                f"Verification issue on '{input_text[:80]}': {verification['issues'][:200]}"
            )

        # ── 7. AUDIT ──
        action_type = AuditAction.CREATE if domain == "development" else AuditAction.EXECUTE
        audit_trail.log(
            action=action_type,
            agent="CoreAI",
            target=input_text[:100],
            description=f"Domain: {domain}, Language: {detected_lang}, Success: {final_success}",
            details={
                "task_id": task_id,
                "domain": domain,
                "language": detected_lang,
                "duration_ms": duration_ms,
                "phases": len(result.get("phases", [])),
            },
        )

        # ── 8. ANALYTICS ──
        analytics.track(
            name="core_task",
            value=1,
            unit="task",
            category=domain,
            tags={"language": detected_lang, "success": str(final_success)},
        )
        analytics.track(
            name="core_duration",
            value=duration_ms,
            unit="ms",
            category=domain,
        )

        # ── 9. REPORT ──
        autonomous_routine.heartbeat()

        return {
            **result,
            "pipeline": {
                "understand": {"language": detected_lang, "language_name": lang_name,
                               "domain": domain},
                "recall": {"prior_knowledge_count": 1 if prior_knowledge else 0,
                           "similar_experiences": len(similar_experiences)},
                "execute": {"status": result.get("status"),
                            "phases": len(result.get("phases", [])),
                            "duration_ms": duration_ms},
                "verify": verification,
                "learn": learning_engine.get_stats(),
                "audit": audit_trail.get_stats(),
            },
        }

    async def _self_heal(
        self, original_task: str, failed_result: dict,
        context: dict, max_retries: int, start_time: float,
    ) -> dict:
        """Attempt to heal a failed task by delegating to the Debugger + Programmer + Tester."""
        for attempt in range(max_retries):
            error_summary = failed_result.get("error", "Unknown error")
            log.info("CoreAI: Self-healing attempt %d/%d — %s",
                     attempt + 1, max_retries, error_summary[:80])

            heal_task = (
                f"Previous attempt to '{original_task}' failed with: {error_summary}. "
                f"Analyze what went wrong, fix the issue, and complete the task. "
                f"Do NOT repeat the same approach that failed."
            )

            heal_result = await self.employee.handle_request(heal_task, context)

            if heal_result.get("status") == "success":
                log.info("CoreAI: Self-healing succeeded on attempt %d", attempt + 1)
                return heal_result

            failed_result = heal_result

        log.warning("CoreAI: Self-healing exhausted after %d retries", max_retries)
        return failed_result

    async def _verify_result(self, task: str, result: dict) -> dict:
        """Verify that the result actually addresses the task."""
        issues = []

        if result.get("status") == "failed":
            issues.append(f"Task failed: {result.get('error', '')[:200]}")
        elif result.get("status") == "partial":
            issues.append("Some phases failed")

        phases = result.get("phases", [])
        failed_phases = [p for p in phases if p.get("status") == "failed"]
        if failed_phases:
            for fp in failed_phases:
                issues.append(
                    f"Phase '{fp.get('agent', 'unknown')}' failed: "
                    f"{fp.get('error', '')[:150]}"
                )

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "issue_count": len(issues),
        }

    async def voice_pipeline(self, audio_text: str,
                             reply_by_voice: bool = False) -> dict:
        """Full voice-to-action pipeline: speech → understand → execute → speak reply."""
        result = await self.think(audio_text)

        if reply_by_voice:
            response_text = result.get("output", "")
            if not response_text:
                response_text = (
                    f"Task completed. Status: {result.get('status', 'unknown')}."
                )
            try:
                from core.voice.tts import tts
                detected = result.get("pipeline", {}).get("understand", {}).get("language", "en")
                await tts.speak_in_language(response_text[:500], lang_code=detected)
                log.info("CoreAI: Voice reply spoken (%s)", detected)
            except Exception as e:
                log.warning("CoreAI: Voice reply failed: %s", e)

        return result

    async def code_task(self, description: str, project_dir: str = "",
                        frameworks: list[str] | None = None) -> dict:
        """Handle a coding-specific task with self-healing enabled by default."""
        context = {}
        if project_dir:
            context["project_dir"] = project_dir
        if frameworks:
            context["frameworks"] = frameworks

        context["task_type"] = "coding"
        return await self.think(description, context, auto_heal=True, max_retries=5)

    async def business_task(self, description: str) -> dict:
        """Handle a business task (sales, marketing, finance, proposals)."""
        context = {"task_type": "business"}
        return await self.think(description, context, auto_heal=False)

    async def creative_task(self, description: str) -> dict:
        """Handle a creative task (design, content, social media)."""
        context = {"task_type": "creative"}
        return await self.think(description, context, auto_heal=False)

    def _classify_domain(self, text: str) -> str:
        t = text.lower()

        if any(w in t for w in ["code", "program", "app", "api", "software", "build",
                                "developer", "database", "server", "website", "backend",
                                "frontend", "migration", "controller", "model",
                                "debug", "test", "fix", "error", "bug", "crash"]):
            return "development"
        if any(w in t for w in ["design", "ui", "ux", "css", "brand", "color", "layout",
                                "logo", "banner", "post", "social media"]):
            return "design"
        if any(w in t for w in ["marketing", "seo", "social", "ad", "campaign",
                                "content", "blog", "post"]):
            return "marketing"
        if any(w in t for w in ["finance", "invoice", "budget", "payment", "tax",
                                "revenue", "cost", "pricing"]):
            return "finance"
        if any(w in t for w in ["security", "vulnerability", "compliance", "audit",
                                "monitor", "encrypt"]):
            return "security"
        if any(w in t for w in ["email", "inbox", "message", "reply", "draft",
                                "newsletter"]):
            return "communication"
        if any(w in t for w in ["customer", "support", "client", "help", "issue",
                                "ticket"]):
            return "support"
        if any(w in t for w in ["sale", "lead", "proposal", "deal", "quote",
                                "negotiate"]):
            return "sales"
        if any(w in t for w in ["deploy", "docker", "kubernetes", "ci/cd",
                                "pipeline", "infrastructure"]):
            return "devops"
        return "general"

    async def status(self) -> dict:
        return {
            **await self.employee.status(),
            "audit": audit_trail.get_stats(),
            "analytics": analytics.stats(),
            "business_memory": business_memory.get_stats(),
            "brain": {
                "working_language": self.working_language,
                "agents": len(self.employee.ceo.agent_manager.list()),
            },
        }


core_ai = CoreAI()
