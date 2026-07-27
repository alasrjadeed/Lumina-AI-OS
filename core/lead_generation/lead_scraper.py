from __future__ import annotations

import asyncio
import re
from typing import Any

from core.log import log
from core.provider import engine as ai_engine

from .apify_client import APIFY_ACTOR_MAP, ApifyClient
from .health import ScraperHealthCheck
from .models import LeadCategory
from .persistence import LeadPersistenceService
from .platform_registry import PlatformRegistry
from .python_scraper_gateway import PythonScraperGateway


class LeadScraperService:
    def __init__(
        self,
        apify_client: ApifyClient | None = None,
        persistence: LeadPersistenceService | None = None,
        registry: PlatformRegistry | None = None,
    ):
        self.python_gateway = PythonScraperGateway()
        self.apify = apify_client or ApifyClient()
        self.persistence = persistence or LeadPersistenceService()
        self.registry = registry or PlatformRegistry()
        self.health = ScraperHealthCheck(self.persistence)

    async def generate_leads(
        self,
        keyword: str,
        location: str = "Bahrain",
        platforms: list[str] | None = None,
        limit: int = 10,
        category_name: str = "",
        use_ai_fallback: bool = True,
    ) -> dict[str, Any]:
        if not platforms:
            country_code = self.registry._find_code(location)
            platforms = self.registry.for_country(country_code)
            platforms = platforms[:12] if len(platforms) > 12 else platforms

        all_leads: list[dict[str, Any]] = []
        platform_results: dict[str, int] = {}

        tasks = [
            self._fetch_for_platform(p, keyword, location, limit)
            for p in platforms
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for platform, result in zip(platforms, results):
            if isinstance(result, Exception):
                log.warning("Platform %s failed: %s", platform, result)
                platform_results[platform] = 0
                continue
            leads = result if isinstance(result, list) else []
            platform_results[platform] = len(leads)
            all_leads.extend(leads)
            await asyncio.sleep(0.1)

        saved_count = 0
        used_ai_fallback = False

        if all_leads:
            saved_count = self.persistence.save_leads(all_leads, category_name=category_name)

        if not all_leads and use_ai_fallback:
            log.info("No leads from scrapers, using AI fallback for: %s in %s", keyword, location)
            ai_leads = await self._ai_fallback(keyword, location, limit)
            if ai_leads:
                saved_count += self.persistence.save_leads(ai_leads, category_name=category_name)
                all_leads.extend(ai_leads)
                used_ai_fallback = True

        return {
            "keyword": keyword,
            "location": location,
            "platforms_used": len(platforms),
            "platforms_results": platform_results,
            "raw_leads_found": len(all_leads),
            "leads_saved": saved_count,
            "uses_ai_fallback": used_ai_fallback,
        }

    async def generate_for_category(
        self,
        category: LeadCategory,
        location: str = "",
    ) -> dict[str, Any]:
        location = location or category.country_code or "Bahrain"
        platforms = category.platforms if category.platforms else self.registry.for_country(
            self.registry._find_code(location)
        )

        total_saved = 0
        results = []

        for keyword in category.keywords:
            result = await self.generate_leads(
                keyword=keyword,
                location=location,
                platforms=platforms,
                limit=category.lead_limit,
                category_name=category.name,
            )
            total_saved += result["leads_saved"]
            results.append(result)

        return {
            "category": category.name,
            "keywords_processed": len(category.keywords),
            "total_leads_saved": total_saved,
            "keyword_results": results,
        }

    async def generate_bulk(
        self,
        keyword: str,
        location: str,
        category_name: str = "",
        limit: int = 10,
    ) -> dict[str, Any]:
        platforms = list(APIFY_ACTOR_MAP.keys())
        from .platform_registry import CLASSIFIED_PLATFORMS, GLOBAL_SCRAPERS
        platforms.extend(CLASSIFIED_PLATFORMS.keys())
        platforms.extend(GLOBAL_SCRAPERS.keys())
        platforms = list(dict.fromkeys(platforms))

        return await self.generate_leads(
            keyword=keyword,
            location=location,
            platforms=platforms,
            limit=limit,
            category_name=category_name,
            use_ai_fallback=True,
        )

    async def enrich_lead(self, lead_id: str) -> dict[str, Any] | None:
        lead = self.persistence.get_lead(lead_id)
        if not lead:
            return None
        if not lead.website:
            return {"enriched": False, "reason": "No website to enrich from"}

        try:
            enriched_data = await self._crawl_website(lead.website)
            if enriched_data.get("emails"):
                if not lead.email:
                    lead.email = enriched_data["emails"][0]
            if enriched_data.get("phones"):
                if not lead.phone:
                    lead.phone = enriched_data["phones"][0]
            if enriched_data.get("description"):
                lead.description = enriched_data["description"]

            lead.enriched = True
            lead.lead_score = min(lead.lead_score + 15, 100)
            self.persistence.update_lead(
                lead.id,
                email=lead.email,
                phone=lead.phone,
                description=lead.description,
                enriched=True,
                lead_score=lead.lead_score,
            )
            return {"enriched": True, "data": enriched_data}

        except Exception as e:
            log.warning("Enrichment failed for %s: %s", lead.website, e)
            return {"enriched": False, "reason": str(e)}

    async def _fetch_for_platform(
        self, platform: str, keyword: str, location: str, limit: int
    ) -> list[dict[str, Any]]:
        if self.health.is_disabled(platform):
            log.info("Platform %s is disabled, skipping", platform)
            return []

        try:
            # Layer 1: Python scraper
            python_leads = await self.python_gateway.scrape(platform, keyword, location, limit)
            if python_leads:
                self.health.record_success(platform)
                return python_leads

            # Layer 2: Apify actor
            apify_leads = await self._fetch_apify(platform, keyword, location, limit)
            if apify_leads:
                self.health.record_success(platform)
                return apify_leads

            self.health.record_success(platform)
            return []

        except Exception as e:
            self.health.record_failure(platform, str(e), "fetch_error")
            return []

    async def _fetch_apify(
        self, platform: str, keyword: str, location: str, limit: int
    ) -> list[dict[str, Any]]:
        apify_info = APIFY_ACTOR_MAP.get(platform)
        if not apify_info or not apify_info.apify_actor:
            return []

        token = self.apify.active_token
        if not token:
            return []

        apify_data: list[dict[str, Any]] = []
        if platform == "google_maps":
            apify_data = await self.apify.fetch_google_maps(keyword, location, limit)
        elif platform == "google_search":
            apify_data = await self.apify.fetch_google_search(keyword, location, limit)
        elif platform == "google_reviews":
            apify_data = await self.apify.fetch_google_reviews(keyword, location, limit)
        elif platform == "ecommerce":
            apify_data = await self.apify.fetch_ecommerce(keyword, limit)

        leads: list[dict[str, Any]] = []
        for item in apify_data[:limit]:
            lead = {
                "source": platform,
                "business_name": item.get("title") or item.get("name") or item.get("businessName", ""),
                "email": item.get("email") or item.get("contactEmail", ""),
                "phone": item.get("phone") or item.get("contactPhone", ""),
                "website": item.get("website") or item.get("url") or item.get("websiteUrl", ""),
                "country": location,
                "category": keyword,
                "description": item.get("description") or item.get("snippet", ""),
                "lead_score": 60,
                "metadata": item,
            }
            if item.get("facebook"):
                lead["social_facebook"] = item["facebook"]
            if item.get("instagram"):
                lead["social_instagram"] = item["instagram"]
            if item.get("twitter"):
                lead["social_twitter"] = item["twitter"]
            leads.append(lead)

        return leads

    async def _ai_fallback(
        self, keyword: str, location: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        try:
            prompt = f"""Generate {limit} realistic business leads for "{keyword}" in {location}.
Return ONLY valid JSON array. Each object must have: business_name, phone(format: +XXX...), email, website, description (20-50 words real description).
Make the data realistic — use real area codes, real street names in {location}, real business names in that country.
Format:
[
  {{"business_name": "Al Jazeera Construction", "phone": "+973 1700 1234", "email": "info@aljazeera-const.bh", "website": "www.aljazeera-const.bh", "description": "..."}}
]"""
            result = await ai_engine.chat([
                {"role": "system", "content": "You are a lead generation AI for GCC businesses. Output valid JSON arrays only."},
                {"role": "user", "content": prompt},
            ])
            content = result.get("message", {}).get("content", "")
            if not content:
                return []

            json_match = re.search(r"\[.*\]", content, re.DOTALL)
            if not json_match:
                return []

            import json
            leads = json.loads(json_match.group(0))
            for lead in leads:
                lead["source"] = "ai_fallback"
                lead["country"] = location
                lead["category"] = keyword
                lead["lead_score"] = 40
            return leads[:limit]
        except Exception as e:
            log.warning("AI fallback failed: %s", e)
            return []

    async def _crawl_website(self, url: str) -> dict[str, Any]:
        import httpx
        if not url.startswith("http"):
            url = f"https://{url}"
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
                resp = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                html = resp.text if resp.status_code == 200 else ""

            emails = list(set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", html)))
            phones = list(set(re.findall(
                r"\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{2,4}", html
            )))
            title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE)
            desc_match = re.search(
                r'<meta\s+name="description"\s+content="([^"]+)"', html, re.IGNORECASE
            )

            return {
                "emails": emails[:3],
                "phones": phones[:3],
                "title": title_match.group(1) if title_match else "",
                "description": desc_match.group(1) if desc_match else "",
            }
        except Exception as e:
            log.debug("Website crawl failed for %s: %s", url, e)
            return {}
