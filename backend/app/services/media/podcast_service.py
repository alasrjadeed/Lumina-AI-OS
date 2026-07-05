import logging
from typing import Any, Dict, List, Optional
from backend.app.services.ai.engine import AIEngine

logger = logging.getLogger(__name__)


class PodcastService:
    def __init__(self, ai: AIEngine):
        self.ai = ai

    async def create_episode(self, title: str, topic: str, duration: str = "20min", style: str = "conversational") -> Dict[str, Any]:
        system = f"Write a {duration} {style} podcast episode script with host dialogue, segments, and transitions."
        script = await self.ai.generate(prompt=f"Podcast episode '{title}' about: {topic}", system=system)
        return {"title": title, "topic": topic, "script": script, "duration": duration, "style": style}

    async def show_notes(self, episode_title: str, transcript: str) -> Dict[str, Any]:
        system = "Create professional show notes with timestamps, key points, and resources."
        notes = await self.ai.generate(prompt=f"Show notes for '{episode_title}':\n{transcript[:8000]}", system=system)
        return {"episode": episode_title, "notes": notes}

    async def interview_questions(self, guest: str, topic: str) -> Dict[str, Any]:
        system = "Generate thoughtful interview questions."
        questions = await self.ai.generate(prompt=f"Interview questions for {guest} about: {topic}", system=system)
        return {"guest": guest, "questions": questions}
