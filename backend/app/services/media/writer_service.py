import logging
from typing import Any, Dict, List, Optional
from backend.app.services.ai.engine import AIEngine

logger = logging.getLogger(__name__)


class WriterService:
    def __init__(self, ai: AIEngine):
        self.ai = ai

    async def write_article(self, topic: str, length: str = "medium", tone: str = "professional", format: str = "article") -> Dict[str, Any]:
        system = f"You are a professional writer. Write a {length} {format} in a {tone} tone with proper structure."
        content = await self.ai.generate(prompt=f"Write a {format} about: {topic}", system=system)
        return {"topic": topic, "content": content, "length": length, "tone": tone, "format": format}

    async def write_book(self, title: str, chapters: List[str], genre: str = "non-fiction") -> Dict[str, Any]:
        system = f"You are an author writing a {genre} book."
        outline = await self.ai.generate(prompt=f"Create detailed outline for '{title}' with chapters: {', '.join(chapters)}", system=system)
        return {"title": title, "chapters": chapters, "outline": outline}

    async def write_script(self, format: str, topic: str, duration: str = "5min") -> Dict[str, Any]:
        system = f"Write a {duration} {format} script."
        script = await self.ai.generate(prompt=f"Write a {format} script about: {topic}", system=system)
        return {"format": format, "topic": topic, "script": script}

    async def edit_content(self, content: str, instructions: str) -> Dict[str, Any]:
        system = "You are an editor. Improve the content based on the instructions."
        edited = await self.ai.generate(prompt=f"Edit this content:\n{content}\n\nInstructions: {instructions}", system=system)
        return {"original_length": len(content), "edited_content": edited}
