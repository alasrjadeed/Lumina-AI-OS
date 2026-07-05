import logging
from typing import Any, Dict, List, Optional
from backend.app.services.ai.engine import AIEngine
from backend.app.services.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class LeadGenerationService:
    def __init__(self, ai: AIEngine, memory: MemoryManager):
        self.ai = ai
        self.memory = memory
        self._namespace = "leads_generated"

    async def search_businesses(self, criteria: str, location: str = "") -> Dict[str, Any]:
        system = "You are a lead generation analyst. Find businesses matching the criteria. Return a JSON list of companies with name, website, industry, and potential contact info."
        prompt = f"Find businesses matching: {criteria}"
        if location:
            prompt += f" in {location}"
        prompt += "\nReturn as JSON array: [{\"company_name\": \"...\", \"website\": \"...\", \"industry\": \"...\", \"notes\": \"...\"}]"
        result = await self.ai.generate_json(prompt=prompt, system=system)
        leads = result if isinstance(result, list) else result.get("leads", result.get("businesses", []))
        stored = []
        for lead in leads[:20]:
            lead["source"] = "ai_generated"
            lead["status"] = "new"
            key = f"generated:{lead.get('company_name', 'unknown')}"
            await self.memory.store(key, lead, namespace=self._namespace)
            stored.append(lead)
        return {"criteria": criteria, "location": location, "leads_found": len(stored), "leads": stored}

    async def enrich_lead(self, company_name: str, website: str = "") -> Dict[str, Any]:
        system = "You are a business researcher. Enrich the company profile with industry, size, technologies used, and potential needs."
        prompt = f"Research and enrich: {company_name}"
        if website:
            prompt += f" ({website})"
        result = await self.ai.generate(prompt=prompt, system=system)
        enrichment = {"company_name": company_name, "website": website, "enrichment": result}
        key = f"enriched:{company_name}"
        await self.memory.store(key, enrichment, namespace=f"{self._namespace}_enriched")
        return enrichment

    async def get_stored_leads(self) -> List[Dict[str, Any]]:
        entries = await self.memory.list_namespace(self._namespace)
        return [e.get("value", {}) for e in entries]
