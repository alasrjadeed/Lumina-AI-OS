"""Autonomous Employee — the main entry point for Lumina's autonomous operation."""

from __future__ import annotations

import time

from core.agents.approval import ApprovalLevel, approval_gate
from core.agents.ceo import CEOAgent, OrchestrationRun
from core.agents.languages import language_engine
from core.agents.learning import learning_engine
from core.agents.routine import autonomous_routine
from core.log import log


class LuminaEmployee:
    """The autonomous digital employee — think, plan, build, talk, learn, work."""

    def __init__(self, ceo: CEOAgent | None = None):
        self.ceo = ceo or CEOAgent()
        self.working_language = "en"

    async def handle_request(self, text: str, context: dict | None = None) -> dict:
        """Process a natural language request through the full Think-Plan-Execute-Verify-Learn
        cycle."""
        start = time.time()

        detected_lang = language_engine.detect(text)
        lang_context = ""
        if detected_lang != self.working_language:
            lang_context = language_engine.build_multilingual_prompt(text)

        prior_knowledge = await learning_engine.get_knowledge_for_task(text)

        full_context = context or {}
        if lang_context:
            full_context["language_prompt"] = lang_context
            full_context["detected_language"] = detected_lang
        if prior_knowledge:
            full_context["prior_knowledge"] = prior_knowledge

        run = await self.ceo.orchestrate(text, full_context)
        duration = (time.time() - start) * 1000

        await learning_engine.record(
            project="autonomous",
            domain=self._detect_domain(text),
            task=text,
            agent="CEO AI",
            approach="Orchestration",
            result=run.output[:500] if run.output else "",
            duration_ms=duration,
            success=run.status == "success",
            learned=self._extract_learning(run),
            tags=self._extract_tags(text),
        )

        await autonomous_routine.add_completed_task(
            agent="CEO AI",
            task=text,
            duration_ms=duration,
            success=run.status == "success",
        )

        autonomous_routine.heartbeat()

        return {
            **run.to_dict(),
            "detected_language": detected_lang,
            "language_name": language_engine.get_name(detected_lang),
            "replied_in": detected_lang,
            "learning": learning_engine.get_stats(),
        }

    async def handle_with_approval(
        self,
        action: str,
        description: str,
        task: str,
        details: dict | None = None,
    ) -> dict:
        """Handle a task that may require human approval before execution."""
        level = approval_gate.get_level(action)

        if level in (ApprovalLevel.AUTO, ApprovalLevel.NOTIFY):
            result = await self.handle_request(task)
            await approval_gate.request(
                action=action,
                agent="CEO AI",
                description=description,
                details=details or {},
            )
            return {"status": "executed", "approval": level.value, **result}

        req = await approval_gate.request(
            action=action,
            agent="CEO AI",
            description=description,
            details=details or {},
        )

        if req.status == "approved":
            result = await self.handle_request(task)
            return {"status": "executed", "approval": req.to_dict(), **result}

        return {
            "status": "pending_approval",
            "approval": req.to_dict(),
            "message": f"Action '{action}' requires your approval before execution.",
        }

    async def morning_routine(self) -> dict:
        """Run the daily morning startup routine."""
        startup = await autonomous_routine.morning_startup()
        log.info("Lumina Employee: Morning routine started")

        stats = learning_engine.get_stats()
        pending = approval_gate.count_pending()

        return {
            **startup,
            "learning": stats,
            "pending_approvals": pending,
            "message": (
                f"Good morning. Lumina is online.\n"
                f"I have learned from {stats['total_experiences']} past experiences "
                f"({stats['success_rate']}% success rate).\n"
                f"{pending} approval(s) pending your review."
            ),
        }

    async def evening_routine(self) -> dict:
        """Run the end-of-day shutdown routine."""
        daily = await learning_engine.generate_daily_summary()
        shutdown = await autonomous_routine.evening_shutdown()
        log.info("Lumina Employee: Evening shutdown complete")

        return {
            **shutdown,
            "daily_learning": daily,
            "message": (f"Good evening. Today's work complete.\n{shutdown['summary']}"),
        }

    async def status(self) -> dict:
        return {
            "language": language_engine.list_languages()[:5],
            "working_language": self.working_language,
            "learning": learning_engine.get_stats(),
            "pending_approvals": approval_gate.count_pending(),
            "routine_status": autonomous_routine.status,
            "agent_count": len(self.ceo.agent_manager.list()),
            "agents": self.ceo.agent_manager.list(),
            "health": self.ceo.agent_manager.health(),
        }

    def _detect_domain(self, text: str) -> str:
        t = text.lower()
        if any(
            w in t
            for w in [
                "code",
                "program",
                "app",
                "api",
                "software",
                "developer",
                "database",
                "server",
            ]
        ):
            return "development"
        if any(w in t for w in ["design", "ui", "css", "brand", "color", "layout"]):
            return "design"
        if any(w in t for w in ["marketing", "seo", "social", "ad", "campaign", "brand"]):
            return "marketing"
        if any(w in t for w in ["finance", "invoice", "budget", "payment", "tax"]):
            return "finance"
        if any(w in t for w in ["security", "vulnerability", "compliance", "audit"]):
            return "security"
        if any(w in t for w in ["email", "inbox", "message", "reply", "draft"]):
            return "communication"
        if any(w in t for w in ["customer", "support", "client", "help", "issue"]):
            return "support"
        if any(w in t for w in ["sale", "lead", "proposal", "deal", "quote"]):
            return "sales"
        return "general"

    def _extract_tags(self, text: str) -> list[str]:
        tags = [self._detect_domain(text)]
        t = text.lower()
        if "python" in t:
            tags.append("python")
        if "react" in t:
            tags.append("react")
        if "fastapi" in t:
            tags.append("fastapi")
        if "docker" in t:
            tags.append("docker")
        if "database" in t:
            tags.append("database")
        return tags

    def _extract_learning(self, run: OrchestrationRun) -> str:
        if run.status == "success":
            return f"Successfully completed: {run.task[:100]}. Agents used: {len(run.phases)}."
        if run.status == "partial":
            return f"Partial success: {run.task[:100]}. Some phases failed."
        return f"Failed: {run.task[:100]}. Error: {run.error[:100]}"


employee = LuminaEmployee()
