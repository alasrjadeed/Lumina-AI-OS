"""AI Project Agent — Lumina agents can read, write, edit, and run code in projects."""

from __future__ import annotations

from core.agents.runner import runner
from core.core_ai import core_ai
from core.projects import project_manager


class ProjectAgent:
    """AI agent that works on a specific project — reads files, writes code, runs commands."""

    def __init__(self, project_id: str):
        proj = project_manager.get(project_id)
        if not proj:
            raise ValueError(f"Project not found: {project_id}")
        self.project = proj
        self.project_id = project_id

    def _project_context(self) -> str:
        """Build context about the project for the AI."""
        proj = self.project
        files = project_manager.list_files(proj.id)[:30]
        file_list = "\n".join(f"  {f.type}/ {f.path}" for f in files[:30])

        return (
            f"Project: {proj.name}\n"
            f"Path: {proj.path}\n"
            f"Framework: {proj.framework}\n"
            f"Language: {proj.language}\n"
            f"Description: {proj.description}\n"
            f"Files ({proj.file_count} total, showing {len(files)}):\n{file_list}\n"
        )

    async def ask(self, task: str) -> dict:
        """Ask the AI to work on this project — full context included."""
        context = {
            "project_context": self._project_context(),
            "project_path": self.project.path,
            "project_id": self.project_id,
        }
        result = await core_ai.think(task, context, auto_heal=True, max_retries=3)

        if result.get("status") == "success" and result.get("phases"):
            for phase in result["phases"]:
                phase.get("agent", "")
                phase_result = phase.get("result", "")
                if not phase_result:
                    continue

        return {
            "project": self.project.to_dict(),
            "result": result,
        }

    async def ask_agent(self, agent_id: str, task: str) -> dict:
        """Ask a specific agent to work on this project."""
        context = {
            "project_context": self._project_context(),
            "project_path": self.project.path,
            "project_id": self.project_id,
        }
        run = await runner.run(agent_id, task, context)
        return {
            "project": self.project.to_dict(),
            "agent_run": run.to_dict(),
        }

    async def read_file(self, file_path: str) -> str:
        result = project_manager.read_file(self.project_id, file_path)
        return result.get("content", "")

    async def write_file(self, file_path: str, content: str) -> dict:
        return project_manager.write_file(self.project_id, file_path, content)

    def get_files(self, sub_path: str = "") -> list:
        return project_manager.list_files(self.project_id, sub_path)
