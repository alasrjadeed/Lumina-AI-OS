import logging
from typing import Any, Dict, List, Optional
from backend.app.services.ai.engine import AIEngine

logger = logging.getLogger(__name__)


class DesignerService:
    def __init__(self, ai: AIEngine):
        self.ai = ai

    async def generate_logo_description(self, brand: str, industry: str, style: str = "modern") -> Dict[str, Any]:
        system = "You are a brand designer. Describe a logo concept in detail."
        desc = await self.ai.generate(prompt=f"Design a {style} logo for {brand} ({industry})", system=system)
        return {"brand": brand, "description": desc, "style": style}

    async def generate_brand_colors(self, brand: str, industry: str) -> Dict[str, Any]:
        system = "You are a brand designer. Recommend a professional color palette."
        palette = await self.ai.generate(prompt=f"Color palette for {brand} ({industry})", system=system)
        return {"brand": brand, "palette": palette}

    async def generate_banner(self, purpose: str, dimensions: str = "1200x630") -> Dict[str, Any]:
        system = "Describe a banner design with layout, colors, typography, and imagery."
        desc = await self.ai.generate(prompt=f"Design a {dimensions} banner for: {purpose}", system=system)
        return {"purpose": purpose, "description": desc, "dimensions": dimensions}
