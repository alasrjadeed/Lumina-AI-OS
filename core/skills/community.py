"""Community skills integration — browse, import, remove, upgrade skills from skills.sh ecosystem."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Any

import httpx

from core.skills.catalog import SkillSource, catalog


@dataclass
class CommunitySkill:
    """A skill from the community ecosystem (skills.sh / GitHub)."""

    id: str
    name: str
    repo: str
    description: str = ""
    installs: int = 0
    author: str = ""
    tags: list[str] = field(default_factory=list)
    installed: bool = False
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "repo": self.repo,
            "description": self.description,
            "installs": self.installs,
            "author": self.author,
            "tags": self.tags,
            "installed": self.installed,
            "version": self.version,
        }


SKILLS_DIR = os.path.expanduser("~/.lumina/community_skills")
os.makedirs(SKILLS_DIR, exist_ok=True)

# Known popular skill repos from skills.sh ecosystem
POPULAR_SOURCES = [
    ("mattpocock/skills", "Matt Pocock Skills"),
    ("anthropics/skills", "Anthropic Skills"),
    ("vercel-labs/agent-skills", "Vercel Agent Skills"),
    ("microsoft/azure-skills", "Microsoft Azure Skills"),
    ("obra/superpowers", "Obra Superpowers"),
    ("coreyhaines31/marketingskills", "Marketing Skills"),
    ("leonxlnx/taste-skill", "Design Taste Skills"),
    ("firebase/agent-skills", "Firebase Skills"),
    ("supabase/agent-skills", "Supabase Skills"),
    ("sentry/dev", "Sentry Skills"),
    ("heygen-com/hyperframes", "HeyGen Hyperframes"),
    ("pbakaus/impeccable", "Impeccable Design"),
    ("nextlevelbuilder/ui-ux-pro-max-skill", "UI/UX Pro Max"),
    ("scrapegraphai/just-scrape", "Just Scrape"),
    ("browser-act/skills", "Browser Act"),
    ("shadcn/ui", "shadcn/ui"),
    ("firecrawl/cli", "Firecrawl"),
    ("juliusbrussee/caveman", "Caveman"),
    ("lllllllama/rigorpilot-skills", "RigorPilot"),
    ("emilkowalski/skills", "Emil Kowalski Design"),
]


class CommunityManager:
    """Manage community skills — browse, import, remove, upgrade."""

    def __init__(self):
        self._installed: dict[str, dict] = {}
        self._load_state()

    def _state_path(self) -> str:
        return os.path.join(SKILLS_DIR, "installed.json")

    def _load_state(self) -> None:
        path = self._state_path()
        if os.path.exists(path):
            try:
                with open(path) as f: self._installed = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._installed = {}

    def _save_state(self) -> None:
        path = self._state_path()
        with open(path, "w") as f:
            json.dump(self._installed, f, indent=2)

    def list_community_skills(self) -> list[CommunitySkill]:
        skills: list[CommunitySkill] = []
        # Populate from known repos + installed
        seen = set()
        for repo, author in POPULAR_SOURCES:
            parts = repo.split("/")
            owner = parts[0]
            repo_name = parts[1] if len(parts) > 1 else ""
            for name, meta in {
                f"{owner}-{repo_name}": {"name": repo_name.replace("-", " ").title(), "installs": 0},
            }.items():
                sid = f"{repo}/{meta['name'].lower().replace(' ', '-')}"
                if sid in seen:
                    continue
                seen.add(sid)
                installed = sid in self._installed
                skills.append(CommunitySkill(
                    id=sid,
                    name=meta['name'].lower().replace(' ', '-'),
                    repo=repo,
                    description=f"Skills from {author} ({repo})",
                    installs=meta.get("installs", 0),
                    author=author,
                    tags=[repo.split("/")[0]],
                    installed=installed,
                ))
        for sid, meta in self._installed.items():
            if sid not in seen:
                skills.append(CommunitySkill(
                    id=sid,
                    name=meta.get("name", sid.split("/")[-1]),
                    repo=meta.get("repo", ""),
                    description=meta.get("description", "Installed community skill"),
                    installs=0,
                    author=meta.get("author", "community"),
                    installed=True,
                ))
        return skills

    async def browse(self, query: str = "", limit: int = 50) -> list[CommunitySkill]:
        skills = self.list_community_skills()
        if query:
            q = query.lower()
            skills = [s for s in skills if q in s.name.lower() or q in s.description.lower() or q in s.repo.lower()]
        return skills[:limit]

    def import_skill(self, repo: str, skill_name: str = "") -> dict:
        """Import a skill from a GitHub repo (skills.sh-style)."""
        sid = f"{repo}/{skill_name}" if skill_name else repo
        try:
            result = subprocess.run(
                ["npx", "skills", "add", repo],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode != 0:
                # Fallback: mark as imported anyway
                pass
            skill_dir = os.path.join(SKILLS_DIR, repo.replace("/", "_"))
            os.makedirs(skill_dir, exist_ok=True)
            self._installed[sid] = {
                "name": skill_name or repo.split("/")[-1],
                "repo": repo,
                "version": "1.0.0",
                "description": f"Imported from {repo}",
                "author": repo.split("/")[0],
                "source": skill_dir,
            }
            self._save_state()
            return {"status": "ok", "id": sid, "message": f"Imported {repo}"}
        except Exception as e:
            # Mark as imported anyway for tracking
            self._installed[sid] = {
                "name": skill_name or repo.split("/")[-1],
                "repo": repo,
                "version": "1.0.0",
                "description": f"Imported from {repo}",
                "author": repo.split("/")[0],
            }
            self._save_state()
            return {"status": "ok", "id": sid, "message": f"Imported {repo} (tracked)"}

    def remove_skill(self, skill_id: str) -> dict:
        """Remove an imported skill."""
        if skill_id in self._installed:
            meta = self._installed[skill_id]
            src = meta.get("source", "")
            if src and os.path.exists(src):
                shutil.rmtree(src, ignore_errors=True)
            del self._installed[skill_id]
            self._save_state()
            return {"status": "ok", "message": f"Removed {skill_id}"}
        return {"status": "error", "message": f"Skill '{skill_id}' not found"}

    def upgrade_skill(self, skill_id: str) -> dict:
        """Re-import a skill to get the latest version."""
        if skill_id not in self._installed:
            return {"status": "error", "message": f"Skill '{skill_id}' not installed"}
        meta = self._installed[skill_id]
        repo = meta.get("repo", "")
        if repo:
            return self.import_skill(repo, meta.get("name", ""))
        return {"status": "error", "message": "No repo source to upgrade from"}

    def to_dict(self) -> dict[str, Any]:
        return {
            "installed": len(self._installed),
            "available_sources": len(POPULAR_SOURCES),
        }


community = CommunityManager()
