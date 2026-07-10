"""Autonomous Employee Routine — daily startup, proactive monitoring, end-of-day reports."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass

ROUTINE_DIR = os.path.expanduser("~/.lumina/routine")


@dataclass
class DailyReport:
    date: str
    tasks_completed: int
    tasks_failed: int
    agents_used: list[str]
    total_duration_ms: float
    highlights: list[str]
    issues: list[str]
    pending_approvals: int
    lessons_learned: list[str]
    created_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "agents_used": self.agents_used,
            "total_duration_ms": self.total_duration_ms,
            "highlights": self.highlights,
            "issues": self.issues,
            "pending_approvals": self.pending_approvals,
            "lessons_learned": self.lessons_learned,
            "created_at": self.created_at,
        }


class AutonomousRoutine:
    """Manages the daily autonomous employee lifecycle."""

    def __init__(self):
        self._reports: list[DailyReport] = []
        self._checklist: list[dict] = []
        self._status = "idle"
        self._last_health_check: float = 0.0
        self._load()

    def _path(self) -> str:
        os.makedirs(ROUTINE_DIR, exist_ok=True)
        return os.path.join(ROUTINE_DIR, "reports.json")

    def _load(self):
        path = self._path()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                for rd in data.get("reports", []):
                    self._reports.append(
                        DailyReport(
                            date=rd["date"],
                            tasks_completed=rd["tasks_completed"],
                            tasks_failed=rd.get("tasks_failed", 0),
                            agents_used=rd.get("agents_used", []),
                            total_duration_ms=rd.get("total_duration_ms", 0),
                            highlights=rd.get("highlights", []),
                            issues=rd.get("issues", []),
                            pending_approvals=rd.get("pending_approvals", 0),
                            lessons_learned=rd.get("lessons_learned", []),
                            created_at=rd.get("created_at", 0),
                        )
                    )
                self._checklist = data.get("checklist", [])
            except Exception:
                pass

    def _save(self):
        with open(self._path(), "w") as f:
            json.dump(
                {
                    "reports": [r.to_dict() for r in self._reports[-30:]],
                    "checklist": self._checklist,
                },
                f,
                indent=2,
            )

    @property
    def status(self) -> str:
        return self._status

    async def morning_startup(self) -> dict:
        """Run the morning startup routine — check status, prioritize, report."""
        self._status = "starting"
        time.time()

        report = DailyReport(
            date=time.strftime("%Y-%m-%d"),
            tasks_completed=0,
            tasks_failed=0,
            agents_used=[],
            total_duration_ms=0,
            highlights=[],
            issues=[],
            pending_approvals=0,
            lessons_learned=[],
            created_at=time.time(),
        )

        self._reports.append(report)
        self._status = "running"
        self._save()

        return {
            "status": "started",
            "date": report.date,
            "message": "Good morning. Lumina is online and ready.",
        }

    async def add_completed_task(
        self,
        agent: str,
        task: str,
        duration_ms: float,
        success: bool,
    ):
        if self._reports:
            r = self._reports[-1]
            if success:
                r.tasks_completed += 1
            else:
                r.tasks_failed += 1
            r.agents_used.append(agent)
            r.total_duration_ms += duration_ms
            if success and len(task) > 10:
                r.highlights.append(task[:120])
            if not success:
                r.issues.append(task[:120])
            self._save()

    async def generate_report(self) -> DailyReport | None:
        if not self._reports:
            return None
        return self._reports[-1]

    def get_report_text(self, report: DailyReport | None = None) -> str:
        r = report or (self._reports[-1] if self._reports else None)
        if not r:
            return "No report available."

        return (
            f"## Daily Report — {r.date}\n\n"
            f"- **Tasks**: {r.tasks_completed} completed, {r.tasks_failed} failed\n"
            f"- **Agents used**: {', '.join(r.agents_used) if r.agents_used else 'none'}\n"
            f"- **Duration**: {r.total_duration_ms / 1000:.1f}s\n"
            f"- **Pending approvals**: {r.pending_approvals}\n\n"
            f"### Highlights\n"
            + "\n".join(f"- {h}" for h in r.highlights[:10])
            + "\n\n"
            + "### Issues\n"
            + "\n".join(f"- {i}" for i in r.issues[:10])
            + "\n\n### Lessons\n"
            + "\n".join(f"- {lesson}" for lesson in r.lessons_learned[:10])
        )

    async def evening_shutdown(self) -> dict:
        """Run end-of-day shutdown — summarize, report, prepare for tomorrow."""
        self._status = "shutting_down"

        report = self._reports[-1] if self._reports else None
        summary = self.get_report_text(report) if report else "No tasks today."

        self._save()
        self._status = "idle"

        return {
            "status": "shutdown",
            "summary": summary,
            "total_tasks": report.tasks_completed if report else 0,
        }

    def set_checklist(self, items: list[dict]):
        self._checklist = items
        self._save()

    def get_checklist(self) -> list[dict]:
        return self._checklist

    def get_reports(self, limit: int = 7) -> list[dict]:
        return [r.to_dict() for r in self._reports[-limit:]]

    def heartbeat(self):
        self._last_health_check = time.time()

    def is_alive(self) -> bool:
        return time.time() - self._last_health_check < 300


autonomous_routine = AutonomousRoutine()
