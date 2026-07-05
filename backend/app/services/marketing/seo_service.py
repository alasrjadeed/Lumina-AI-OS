import logging
from typing import Any, Dict, List, Optional
from backend.app.services.ai.engine import AIEngine

logger = logging.getLogger(__name__)


class SEOService:
    def __init__(self, ai: AIEngine):
        self.ai = ai

    async def analyze_page(self, url: str, content: str) -> Dict[str, Any]:
        system = "You are an SEO expert. Analyze the page for SEO improvements."
        analysis = await self.ai.generate(prompt=f"SEO analysis for {url}:\n{content[:5000]}", system=system)
        return {"url": url, "analysis": analysis}

    async def generate_meta_tags(self, title: str, description: str, keywords: List[str]) -> Dict[str, Any]:
        return {
            "title": title[:60],
            "description": description[:160],
            "keywords": ", ".join(keywords[:10]),
            "og_title": title,
            "og_description": description[:160],
        }

    async def suggest_keywords(self, topic: str, niche: str = "") -> Dict[str, Any]:
        system = "You are an SEO keyword researcher. Suggest high-value keywords."
        suggestions = await self.ai.generate(prompt=f"Suggest SEO keywords for topic '{topic}' in niche '{niche}'", system=system)
        return {"topic": topic, "keywords": suggestions}

    async def audit(self, url: str) -> Dict[str, Any]:
        system = "You are an SEO auditor. Provide a comprehensive SEO audit."
        audit = await self.ai.generate(prompt=f"Perform SEO audit for: {url}", system=system)
        return {"url": url, "audit": audit}
