import logging
from typing import Any, Dict, List, Optional
from backend.app.services.ai.engine import AIEngine

logger = logging.getLogger(__name__)


class VideoService:
    def __init__(self, ai: AIEngine):
        self.ai = ai

    async def create_script(self, topic: str, duration: str = "5min", style: str = "educational") -> Dict[str, Any]:
        system = f"Write a {style} video script with timestamps, visual directions, and speaking parts."
        script = await self.ai.generate(prompt=f"Write a {duration} video script about: {topic}", system=system)
        return {"topic": topic, "duration": duration, "script": script, "style": style}

    async def storyboard(self, script: str) -> Dict[str, Any]:
        system = "Create a visual storyboard from the script. Describe each scene, camera angle, and transition."
        board = await self.ai.generate(prompt=f"Create storyboard from:\n{script[:5000]}", system=system)
        return {"storyboard": board}

    async def thumbnail_description(self, title: str, style: str = "modern") -> Dict[str, Any]:
        system = "Describe a compelling video thumbnail design."
        desc = await self.ai.generate(prompt=f"Thumbnail for video titled: {title}. Style: {style}", system=system)
        return {"title": title, "description": desc}

    async def seo_metadata(self, title: str, description: str) -> Dict[str, Any]:
        return {
            "title": title[:60],
            "description": description[:160],
            "tags": [w.strip() for w in title.split()[:5]],
            "category": "Education",
        }
