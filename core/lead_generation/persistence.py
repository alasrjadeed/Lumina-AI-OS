from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict
from typing import Any

from core.log import log

from .models import GenerationError, LeadCategory, LeadRecord, ScraperStatus

STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "")


class LeadPersistenceService:
    def __init__(self, storage_path: str = ""):
        self._storage_path = storage_path or os.path.join(STORAGE_DIR, "leads_plugin_data.json")
        self._categories_path = os.path.join(STORAGE_DIR, "lead_categories.json")
        self._health_path = os.path.join(STORAGE_DIR, "scraper_health.json")
        self._errors_path = os.path.join(STORAGE_DIR, "generation_errors.json")

    def save_leads(
        self,
        leads: list[dict[str, Any]],
        category_name: str = "",
        category_id: str | None = None,
    ) -> int:
        existing_leads = self._load_leads()
        existing_emails: set[str] = set()
        existing_websites: set[str] = set()
        existing_website_hashes: set[str] = set()
        existing_phone_hashes: set[str] = set()

        for lead in existing_leads.values():
            if lead.email:
                existing_emails.add(lead.email.lower().strip())
            if lead.website:
                existing_websites.add(self._normalize_url(lead.website))
            if lead.website_hash:
                existing_website_hashes.add(lead.website_hash)
            if lead.phone_hash:
                existing_phone_hashes.add(lead.phone_hash)

        saved = 0
        for raw in leads:
            if not raw.get("business_name") and not raw.get("name"):
                continue

            email = (raw.get("email") or "").lower().strip()
            website = self._normalize_url(raw.get("website") or raw.get("url") or "")
            phone = (raw.get("phone") or raw.get("phone_number") or "").strip()
            website_hash = self._compute_hash(website) if website else ""
            phone_hash = self._compute_hash(self._normalize_phone(phone)) if phone else ""

            if email and email in existing_emails:
                continue
            if website and website in existing_websites:
                continue
            if website_hash and website_hash in existing_website_hashes:
                continue
            if phone_hash and phone_hash in existing_phone_hashes:
                continue

            lead = LeadRecord(
                id=f"lead_{int(time.time() * 1000)}_{saved}",
                business_name=raw.get("business_name") or raw.get("name") or raw.get("title", ""),
                email=email,
                phone=phone,
                website=website,
                source=raw.get("source") or raw.get("platform", ""),
                category=category_name or raw.get("category", ""),
                country=raw.get("country") or raw.get("location", ""),
                city=raw.get("city", ""),
                description=raw.get("description") or raw.get("snippet", ""),
                lead_type=self._classify(raw, category_name),
                lead_score=self._score_lead(raw),
                social_facebook=raw.get("social_facebook", ""),
                social_instagram=raw.get("social_instagram", ""),
                social_tiktok=raw.get("social_tiktok", ""),
                social_youtube=raw.get("social_youtube", ""),
                social_linkedin=raw.get("social_linkedin", ""),
                social_twitter=raw.get("social_twitter", ""),
                website_hash=website_hash,
                phone_hash=phone_hash,
                contact_person=raw.get("contact_person", ""),
                address=raw.get("address", ""),
                rating=raw.get("rating", 0.0),
                reviews_count=raw.get("reviews_count", 0),
                tags=raw.get("tags", []),
                social_links=raw.get("social_links", {}),
                gm_data=raw.get("gm_data", {}),
                gm_categories=raw.get("gm_categories", []),
                additional_info=raw.get("additional_info", {}),
                enriched_data=raw.get("enriched_data", {}),
                whatsapp_phone=raw.get("whatsapp_phone", ""),
                location_coords=raw.get("location_coords", {}),
                map_url=raw.get("map_url", ""),
                opening_hours=raw.get("opening_hours", []),
                platform_profile_name=raw.get("platform_profile_name", ""),
                followers_count=raw.get("followers_count", 0),
                engagement_count=raw.get("engagement_count", 0),
                last_post_content=raw.get("last_post_content", ""),
                source_url=raw.get("source_url", ""),
                metadata=raw.get("metadata", {}),
            )

            existing_leads[lead.id] = lead
            if email:
                existing_emails.add(email)
            if website:
                existing_websites.add(website)
            if website_hash:
                existing_website_hashes.add(website_hash)
            if phone_hash:
                existing_phone_hashes.add(phone_hash)
            saved += 1

        self._save_leads(existing_leads)
        log.info("Saved %d new leads (total: %d, deduped: %d)", saved, len(existing_leads), len(leads) - saved)
        return saved

    def get_leads(
        self,
        status: str = "",
        source: str = "",
        category: str = "",
        country: str = "",
        lead_type: str = "",
        limit: int = 100,
        offset: int = 0,
    ) -> list[LeadRecord]:
        leads = list(self._load_leads().values())
        if status:
            leads = [l for l in leads if l.status == status]
        if source:
            leads = [l for l in leads if l.source == source]
        if category:
            leads = [l for l in leads if category.lower() in l.category.lower()]
        if country:
            leads = [l for l in leads if country.lower() in l.country.lower()]
        if lead_type:
            leads = [l for l in leads if l.lead_type == lead_type]
        leads.sort(key=lambda l: l.lead_score, reverse=True)
        return leads[offset : offset + limit]

    def count_leads(
        self,
        status: str = "",
        source: str = "",
        category: str = "",
        country: str = "",
        lead_type: str = "",
    ) -> int:
        leads = list(self._load_leads().values())
        if status:
            leads = [l for l in leads if l.status == status]
        if source:
            leads = [l for l in leads if l.source == source]
        if category:
            leads = [l for l in leads if category.lower() in l.category.lower()]
        if country:
            leads = [l for l in leads if country.lower() in l.country.lower()]
        if lead_type:
            leads = [l for l in leads if l.lead_type == lead_type]
        return len(leads)

    def get_lead(self, lead_id: str) -> LeadRecord | None:
        return self._load_leads().get(lead_id)

    def update_lead(self, lead_id: str, **updates: Any) -> LeadRecord | None:
        leads = self._load_leads()
        lead = leads.get(lead_id)
        if not lead:
            return None
        for key, value in updates.items():
            if hasattr(lead, key):
                setattr(lead, key, value)
        lead.updated = time.time()
        self._save_leads(leads)
        return lead

    def update_status(self, lead_id: str, status: str) -> bool:
        leads = self._load_leads()
        lead = leads.get(lead_id)
        if not lead:
            return False
        lead.status = status
        lead.updated = time.time()
        self._save_leads(leads)
        return True

    def bulk_update_status(self, lead_ids: list[str], status: str) -> int:
        leads = self._load_leads()
        count = 0
        for lid in lead_ids:
            if lid in leads:
                leads[lid].status = status
                leads[lid].updated = time.time()
                count += 1
        self._save_leads(leads)
        return count

    def delete_lead(self, lead_id: str) -> bool:
        leads = self._load_leads()
        if lead_id in leads:
            del leads[lead_id]
            self._save_leads(leads)
            return True
        return False

    def bulk_delete(self, lead_ids: list[str]) -> int:
        leads = self._load_leads()
        count = 0
        for lid in lead_ids:
            if lid in leads:
                del leads[lid]
                count += 1
        self._save_leads(leads)
        return count

    def search_leads(self, query: str, limit: int = 50) -> list[LeadRecord]:
        q = query.lower()
        results = [
            l for l in self._load_leads().values()
            if q in l.business_name.lower()
            or q in l.email.lower()
            or q in l.phone.lower()
            or q in l.website.lower()
            or q in l.category.lower()
            or q in l.description.lower()
        ]
        results.sort(key=lambda l: l.lead_score, reverse=True)
        return results[:limit]

    def get_analytics(self) -> dict[str, Any]:
        leads = list(self._load_leads().values())
        total = len(leads)
        by_source: dict[str, int] = {}
        by_status: dict[str, int] = {}
        by_type: dict[str, int] = {}
        by_country: dict[str, int] = {}
        for lead in leads:
            by_source[lead.source] = by_source.get(lead.source, 0) + 1
            by_status[lead.status] = by_status.get(lead.status, 0) + 1
            by_type[lead.lead_type] = by_type.get(lead.lead_type, 0) + 1
            if lead.country:
                by_country[lead.country] = by_country.get(lead.country, 0) + 1
        return {
            "total_leads": total,
            "by_source": by_source,
            "by_status": by_status,
            "by_type": by_type,
            "by_country": by_country,
            "avg_score": sum(l.lead_score for l in leads) / total if total else 0,
            "conversion_rate": (by_status.get("won", 0) / total * 100) if total else 0,
        }

    def get_categories(self) -> list[LeadCategory]:
        if not os.path.exists(self._categories_path):
            return self._default_categories()
        try:
            with open(self._categories_path) as f:
                data = json.load(f)
            return [LeadCategory(**c) for c in data.get("categories", [])]
        except Exception:
            return self._default_categories()

    def save_category(self, category: LeadCategory) -> LeadCategory:
        categories = self.get_categories()
        existing = next((c for c in categories if c.id == category.id), None)
        if existing:
            idx = categories.index(existing)
            categories[idx] = category
        else:
            category.id = category.id or f"cat_{int(time.time())}"
            categories.append(category)
        self._save_categories(categories)
        return category

    def delete_category(self, category_id: str) -> bool:
        categories = self.get_categories()
        filtered = [c for c in categories if c.id != category_id]
        if len(filtered) < len(categories):
            self._save_categories(filtered)
            return True
        return False

    def record_scraper_success(self, platform: str) -> None:
        health = self._load_health()
        entry = health.get(platform, ScraperStatus(platform=platform))
        entry.success_count += 1
        entry.consecutive_failures = 0
        entry.last_success = time.time()
        entry.status = "healthy"
        health[platform] = entry
        self._save_health(health)

    def record_scraper_failure(self, platform: str, error: str = "", error_type: str = "") -> None:
        health = self._load_health()
        entry = health.get(platform, ScraperStatus(platform=platform))
        entry.failure_count += 1
        entry.consecutive_failures += 1
        entry.last_failure = time.time()
        entry.last_error = error[:500] if error else ""
        entry.status = "failing" if entry.consecutive_failures < 10 else "disabled"
        health[platform] = entry
        self._save_health(health)

        if error:
            self._save_error(platform, "", "", error, error_type)

    def get_scraper_health(self) -> dict[str, ScraperStatus]:
        return self._load_health()

    def get_errors(self, limit: int = 50) -> list[GenerationError]:
        if not os.path.exists(self._errors_path):
            return []
        try:
            with open(self._errors_path) as f:
                return [GenerationError(**e) for e in json.load(f)[-limit:]]
        except Exception:
            return []

    def count(self) -> int:
        return len(self._load_leads())

    def _load_leads(self) -> dict[str, LeadRecord]:
        if not os.path.exists(self._storage_path):
            return {}
        try:
            with open(self._storage_path) as f:
                data = json.load(f)
            return {k: LeadRecord(**v) for k, v in data.get("leads", {}).items()}
        except Exception:
            return {}

    def _save_leads(self, leads: dict[str, LeadRecord]) -> None:
        data = {
            "leads": {lid: asdict(lead) for lid, lead in leads.items()},
        }
        with open(self._storage_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _save_categories(self, categories: list[LeadCategory]) -> None:
        with open(self._categories_path, "w") as f:
            json.dump({"categories": [asdict(c) for c in categories]}, f, indent=2, default=str)

    def _load_health(self) -> dict[str, ScraperStatus]:
        if not os.path.exists(self._health_path):
            return {}
        try:
            with open(self._health_path) as f:
                data = json.load(f)
            return {k: ScraperStatus(**v) for k, v in data.items()}
        except Exception:
            return {}

    def _save_health(self, health: dict[str, ScraperStatus]) -> None:
        with open(self._health_path, "w") as f:
            json.dump({k: asdict(v) for k, v in health.items()}, f, indent=2, default=str)

    def _save_error(self, platform: str, keyword: str, location: str, error: str, error_type: str) -> None:
        existing: list[dict[str, Any]] = []
        if os.path.exists(self._errors_path):
            try:
                with open(self._errors_path) as f:
                    existing = json.load(f)
            except Exception:
                pass
        existing.append(asdict(GenerationError(
            platform=platform, keyword=keyword, location=location,
            error_message=error[:1000], error_type=error_type,
        )))
        if len(existing) > 500:
            existing = existing[-500:]
        with open(self._errors_path, "w") as f:
            json.dump(existing, f, indent=2, default=str)

    def _classify(self, raw: dict[str, Any], category: str = "") -> str:
        name = (raw.get("business_name") or raw.get("name") or "").lower()
        desc = (raw.get("description") or raw.get("snippet") or "").lower()
        combined = f"{name} {desc} {category}".lower()
        provider_keywords = ["service", "company", "agency", "firm", "provider", "supplier", "contractor", "consultant", "clinic", "hotel", "restaurant", "shop", "store", "salon", "garage", "repair"]
        if any(kw in combined for kw in provider_keywords):
            return "provider"
        if "business" in combined or "company" in combined:
            return "business"
        return "unknown"

    def _score_lead(self, raw: dict[str, Any]) -> int:
        score = 0
        if raw.get("email"):
            score += 20
        if raw.get("phone") or raw.get("phone_number"):
            score += 15
        if raw.get("website") or raw.get("url"):
            score += 25
        if raw.get("social_facebook") or raw.get("social_instagram") or raw.get("social_linkedin"):
            score += 10
        if raw.get("description") and len(raw.get("description", "")) > 30:
            score += 10
        if raw.get("lead_score"):
            score += raw["lead_score"]
        return min(score, 100)

    @staticmethod
    def _compute_hash(value: str) -> str:
        if not value:
            return ""
        return hashlib.sha256(value.strip().lower().encode()).hexdigest()

    @staticmethod
    def _normalize_url(url: str) -> str:
        if not url:
            return ""
        url = url.strip().lower()
        url = url.replace("https://", "").replace("http://", "").replace("www.", "")
        url = url.rstrip("/")
        return url

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        if not phone:
            return ""
        return "".join(c for c in phone if c.isdigit() or c == "+")

    @staticmethod
    def _default_categories() -> list[LeadCategory]:
        return [
            LeadCategory(id="cat_1", name="Restaurants", keywords=["restaurant", "food", "dining", "cafe"], country_code="BH", priority=1),
            LeadCategory(id="cat_2", name="Construction", keywords=["construction", "building", "contractor", "renovation"], country_code="BH", priority=2),
            LeadCategory(id="cat_3", name="Retail", keywords=["retail", "shop", "store", "wholesale"], country_code="BH", priority=3),
            LeadCategory(id="cat_4", name="Healthcare", keywords=["clinic", "doctor", "hospital", "pharmacy", "medical"], country_code="BH", priority=4),
            LeadCategory(id="cat_5", name="IT Services", keywords=["software", "IT", "technology", "web development", "app"], country_code="BH", priority=5),
            LeadCategory(id="cat_6", name="Real Estate", keywords=["real estate", "property", "broker", "apartment", "villa"], country_code="BH", priority=6),
            LeadCategory(id="cat_7", name="Automotive", keywords=["car", "auto", "repair", "garage", "mechanic"], country_code="BH", priority=7),
            LeadCategory(id="cat_8", name="Beauty & Wellness", keywords=["salon", "spa", "beauty", "barber", "gym", "fitness"], country_code="BH", priority=8),
        ]
