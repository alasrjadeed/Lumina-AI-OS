import logging
from typing import Any, Dict, List, Optional
from backend.app.services.ai.engine import AIEngine

logger = logging.getLogger(__name__)


class ContentService:
    def __init__(self, ai: AIEngine):
        self.ai = ai

    async def write_blog(self, topic: str, tone: str = "professional", length: str = "medium") -> Dict[str, Any]:
        system = f"You are a content writer. Write a {tone} blog post ({length} length) with headings and bullet points."
        content = await self.ai.generate(prompt=f"Write a blog post about: {topic}", system=system)
        return {"topic": topic, "content": content, "tone": tone, "length": length}

    async def write_social_post(self, platform: str, topic: str, tone: str = "casual") -> Dict[str, Any]:
        system = f"Write a {tone} social media post for {platform}. Use appropriate hashtags and formatting."
        content = await self.ai.generate(prompt=f"Create a {platform} post about: {topic}", system=system)
        return {"platform": platform, "content": content, "tone": tone}

    async def write_landing_page(self, product: str, audience: str, usp: str) -> Dict[str, Any]:
        system = "You are a conversion copywriter. Write persuasive landing page copy."
        content = await self.ai.generate(prompt=f"Landing page for {product}. Target: {audience}. USP: {usp}", system=system)
        return {"product": product, "content": content}

    async def write_product_description(self, product: str, features: List[str]) -> Dict[str, Any]:
        system = "Write compelling product descriptions that sell."
        content = await self.ai.generate(prompt=f"Product: {product}\nFeatures: {', '.join(features)}", system=system)
        return {"product": product, "content": content}
