import logging
from enum import Enum
from typing import Any, Dict, List, Optional

from backend.app.services.ai.engine import AIEngine

logger = logging.getLogger(__name__)


class ExplainLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


class ExplainMode(str, Enum):
    TEXT = "text"
    VOICE = "voice"
    BOTH = "text_and_voice"


class ExplainService:
    def __init__(self, ai_engine: AIEngine):
        self.ai_engine = ai_engine
        self._level_prompts = {
            ExplainLevel.BEGINNER: "Use simple language, avoid jargon, explain like I'm new to this.",
            ExplainLevel.INTERMEDIATE: "Use technical detail but keep it accessible.",
            ExplainLevel.EXPERT: "Provide professional explanation with architecture, implementation details, and best practices.",
        }

    async def explain_text(
        self,
        topic: str,
        level: ExplainLevel = ExplainLevel.INTERMEDIATE,
        mode: ExplainMode = ExplainMode.TEXT,
    ) -> Dict[str, Any]:
        system = self._level_prompts[level]
        system += " Include examples and code snippets where appropriate."
        if mode in (ExplainMode.VOICE, ExplainMode.BOTH):
            system += " Structure response for both speech and text display."

        content = await self.ai_engine.generate(
            prompt=f"Explain: {topic}",
            system=system,
        )
        return {
            "topic": topic,
            "level": level.value,
            "content": content,
            "mode": mode.value,
        }

    async def explain_code(
        self,
        code: str,
        language: str = "",
        level: ExplainLevel = ExplainLevel.INTERMEDIATE,
    ) -> Dict[str, Any]:
        system = self._level_prompts[level]
        system += " Explain every line or section. Identify possible improvements. Warn about potential bugs."

        explanation = await self.ai_engine.generate(
            prompt=f"Explain this {language} code:\n```{language}\n{code}\n```",
            system=system,
        )
        return {
            "language": language,
            "code": code,
            "level": level.value,
            "explanation": explanation,
        }

    async def explain_document(
        self,
        content: str,
        filename: str = "",
        level: ExplainLevel = ExplainLevel.INTERMEDIATE,
    ) -> Dict[str, Any]:
        system = self._level_prompts[level]
        system += " Read the document, explain each section, answer likely questions, highlight important points."

        explanation = await self.ai_engine.generate(
            prompt=f"Explain this document '{filename}':\n{content[:8000]}",
            system=system,
        )
        return {
            "filename": filename,
            "level": level.value,
            "explanation": explanation,
        }

    async def explain_website(
        self,
        url: str,
        page_content: str,
        level: ExplainLevel = ExplainLevel.INTERMEDIATE,
    ) -> Dict[str, Any]:
        system = self._level_prompts[level]
        system += " Summarize the webpage, explain difficult concepts."

        explanation = await self.ai_engine.generate(
            prompt=f"Explain this webpage at {url}:\n{page_content[:8000]}",
            system=system,
        )
        return {
            "url": url,
            "level": level.value,
            "explanation": explanation,
        }

    async def explain_report(
        self,
        report_type: str,
        report_data: str,
        level: ExplainLevel = ExplainLevel.INTERMEDIATE,
    ) -> Dict[str, Any]:
        system = self._level_prompts[level]
        system += " Convert technical information into plain language. Highlight key metrics and insights."

        explanation = await self.ai_engine.generate(
            prompt=f"Explain this {report_type} report in plain language:\n{report_data[:8000]}",
            system=system,
        )
        return {
            "report_type": report_type,
            "level": level.value,
            "explanation": explanation,
        }
