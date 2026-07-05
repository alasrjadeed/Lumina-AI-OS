import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path

from backend.app.services.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


@dataclass
class ProjectContext:
    name: str
    architecture: str = ""
    folder_structure: str = ""
    database_schema: str = ""
    apis: List[str] = field(default_factory=list)
    coding_standards: str = ""
    client_requirements: str = ""
    branding: str = ""
    previous_decisions: List[str] = field(default_factory=list)
    bugs_fixed: List[str] = field(default_factory=list)
    pending_tasks: List[str] = field(default_factory=list)
    tech_stack: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "architecture": self.architecture,
            "folder_structure": self.folder_structure,
            "database_schema": self.database_schema,
            "apis": self.apis,
            "coding_standards": self.coding_standards,
            "client_requirements": self.client_requirements,
            "branding": self.branding,
            "previous_decisions": self.previous_decisions,
            "bugs_fixed": self.bugs_fixed,
            "pending_tasks": self.pending_tasks,
            "tech_stack": self.tech_stack,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class WorkMemory:
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager

    async def open_project(self, project_name: str) -> Optional[ProjectContext]:
        data = await self.memory.retrieve(f"project:{project_name}", namespace="work_memory")
        if data:
            ctx = ProjectContext(name=project_name, **{k: v for k, v in data.items() if k != "name"})
            logger.info(f"Restored project context: {project_name}")
            return ctx
        return None

    async def save_project(self, context: ProjectContext):
        await self.memory.store(
            key=f"project:{context.name}",
            value=context.to_dict(),
            namespace="work_memory",
            metadata={"type": "project_context", "updated": context.updated_at.isoformat()},
        )
        logger.info(f"Saved project context: {context.name}")

    async def list_projects(self) -> List[str]:
        entries = await self.memory.list_namespace("work_memory")
        return [e["key"].replace("project:", "") for e in entries if e["key"].startswith("project:")]

    async def add_decision(self, project_name: str, decision: str):
        ctx = await self.open_project(project_name)
        if ctx:
            ctx.previous_decisions.append(decision)
            ctx.updated_at = datetime.now(timezone.utc)
            await self.save_project(ctx)

    async def add_bug_fix(self, project_name: str, bug: str):
        ctx = await self.open_project(project_name)
        if ctx:
            ctx.bugs_fixed.append(bug)
            ctx.updated_at = datetime.now(timezone.utc)
            await self.save_project(ctx)

    async def add_pending_task(self, project_name: str, task: str):
        ctx = await self.open_project(project_name)
        if ctx:
            ctx.pending_tasks.append(task)
            ctx.updated_at = datetime.now(timezone.utc)
            await self.save_project(ctx)

    async def complete_task(self, project_name: str, task: str):
        ctx = await self.open_project(project_name)
        if ctx and task in ctx.pending_tasks:
            ctx.pending_tasks.remove(task)
            ctx.updated_at = datetime.now(timezone.utc)
            await self.save_project(ctx)

    async def project_summary(self, project_name: str) -> str:
        ctx = await self.open_project(project_name)
        if not ctx:
            return f"No project context found for '{project_name}'."
        parts = [
            f"# {ctx.name}",
            f"Architecture: {ctx.architecture or 'Not documented'}",
            f"Database: {ctx.database_schema or 'Not documented'}",
            f"APIs: {len(ctx.apis)} endpoints",
            f"Decisions made: {len(ctx.previous_decisions)}",
            f"Bugs fixed: {len(ctx.bugs_fixed)}",
            f"Pending tasks: {len(ctx.pending_tasks)}",
        ]
        return "\n".join(parts)
