from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

LEAD_STATUSES = ["new", "contacted", "qualified", "proposal", "negotiation", "won", "lost"]

LEAD_TYPES = ["provider", "business", "individual", "unknown"]

GENERATION_SOURCES = [
    "apify", "python_scraper", "ai_fallback", "manual", "whatsapp_import", "csv_import",
]

GCC_COUNTRIES = [
    "BH", "SA", "AE", "QA", "KW", "OM", "EG", "JO", "LB", "PK", "IN", "PH",
]


@dataclass
class CountryInfo:
    code: str
    name: str
    dial_code: str
    currency: str
    domain: str
    classifieds: list[str] = field(default_factory=list)


COUNTRY_METADATA: dict[str, CountryInfo] = {
    "BH": CountryInfo("BH", "Bahrain", "+973", "BHD", ".bh"),
    "SA": CountryInfo("SA", "Saudi Arabia", "+966", "SAR", ".sa"),
    "AE": CountryInfo("AE", "UAE", "+971", "AED", ".ae"),
    "QA": CountryInfo("QA", "Qatar", "+974", "QAR", ".qa"),
    "KW": CountryInfo("KW", "Kuwait", "+965", "KWD", ".kw"),
    "OM": CountryInfo("OM", "Oman", "+968", "OMR", ".om"),
    "EG": CountryInfo("EG", "Egypt", "+20", "EGP", ".eg"),
    "JO": CountryInfo("JO", "Jordan", "+962", "JOD", ".jo"),
    "LB": CountryInfo("LB", "Lebanon", "+961", "LBP", ".lb"),
    "PK": CountryInfo("PK", "Pakistan", "+92", "PKR", ".pk"),
    "IN": CountryInfo("IN", "India", "+91", "INR", ".in"),
    "PH": CountryInfo("PH", "Philippines", "+63", "PHP", ".ph"),
}

COUNTRY_CLASSIFIEDS_MAP: dict[str, list[str]] = {
    "BH": ["expatriates", "opensooq", "olx", "dcciinfo", "abcgcc", "arabiantalks", "bahrainyellow", "gumtree"],
    "SA": ["expatriates", "haraj", "opensooq", "bayt", "gulftalent", "arabiantalks"],
    "AE": ["dubizzle", "bayut", "expatriates", "opensooq", "bayt", "gulftalent", "gumtree", "craigslist"],
    "QA": ["expatriates", "opensooq", "bayt", "gulftalent", "arabiantalks"],
    "KW": ["expatriates", "opensooq", "olx", "bayt", "gulftalent", "arabiantalks"],
    "OM": ["expatriates", "opensooq", "bayt", "gulftalent", "abcgcc"],
    "EG": ["expatriates", "opensooq", "olx", "bayt"],
    "JO": ["expatriates", "opensooq", "bayt"],
    "LB": ["expatriates", "bayt"],
    "PK": ["bayt"],
    "IN": ["bayt", "gulftalent", "justdial", "sulekha"],
    "PH": ["bayt", "gulftalent"],
}


@dataclass
class LeadRecord:
    id: str = ""
    business_name: str = ""
    email: str = ""
    phone: str = ""
    website: str = ""
    source: str = ""
    category: str = ""
    country: str = ""
    city: str = ""
    description: str = ""
    lead_type: str = "unknown"
    lead_score: int = 0
    status: str = "new"
    social_facebook: str = ""
    social_instagram: str = ""
    social_tiktok: str = ""
    social_youtube: str = ""
    social_linkedin: str = ""
    social_twitter: str = ""
    website_hash: str = ""
    phone_hash: str = ""
    enriched: bool = False
    outreach_count: int = 0
    notes: str = ""
    contact_person: str = ""
    address: str = ""
    rating: float = 0.0
    reviews_count: int = 0
    tags: list[str] = field(default_factory=list)
    social_links: dict[str, str] = field(default_factory=dict)
    gm_data: dict[str, Any] = field(default_factory=dict)
    gm_categories: list[str] = field(default_factory=list)
    additional_info: dict[str, Any] = field(default_factory=dict)
    enriched_data: dict[str, Any] = field(default_factory=dict)
    whatsapp_phone: str = ""
    last_contacted_at: float = 0.0
    location_coords: dict[str, float] = field(default_factory=dict)
    map_url: str = ""
    opening_hours: list[dict[str, str]] = field(default_factory=list)
    platform_profile_name: str = ""
    followers_count: int = 0
    engagement_count: int = 0
    last_post_content: str = ""
    source_url: str = ""
    created: float = field(default_factory=time.time)
    updated: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def score_tier(self) -> str:
        if self.lead_score >= 70:
            return "hot"
        elif self.lead_score >= 30:
            return "warm"
        return "cold"

    def to_dict(self) -> dict[str, Any]:
        from dataclasses import asdict
        d = asdict(self)
        d["score_tier"] = self.score_tier
        return d


@dataclass
class LeadCategory:
    id: str = ""
    name: str = ""
    keywords: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=list)
    country_code: str = ""
    priority: int = 0
    active: bool = True
    lead_limit: int = 10
    auto_enrich: bool = True
    min_score_threshold: int = 30
    target_audience: str = ""
    notes: str = ""
    progress: int = 0
    leads_generated: int = 0
    leads_qualified: int = 0
    last_generated_at: float = 0.0
    created: float = field(default_factory=time.time)


@dataclass
class PlatformInfo:
    key: str
    name: str
    category: str = "general"
    scraper_type: str = "apify"
    apify_actor: str = ""
    enabled: bool = True
    requires_auth: bool = False


@dataclass
class ScraperStatus:
    platform: str
    success_count: int = 0
    failure_count: int = 0
    consecutive_failures: int = 0
    last_success: float = 0.0
    last_failure: float = 0.0
    last_error: str = ""
    status: str = "unknown"


@dataclass
class GenerationError:
    platform: str = ""
    keyword: str = ""
    location: str = ""
    error_message: str = ""
    error_type: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class OutreachRecord:
    id: str = ""
    lead_id: str = ""
    channel: str = "email"
    subject: str = ""
    message: str = ""
    status: str = "pending"
    sent_at: float = 0.0
    response: str = ""


@dataclass
class WhatsAppImport:
    id: str = ""
    group_name: str = ""
    contact_count: int = 0
    lead_count: int = 0
    imported_at: float = field(default_factory=time.time)


@dataclass
class LeadExport:
    format: str = "csv"
    lead_ids: list[str] = field(default_factory=list)
    filename: str = ""
    exported_at: float = field(default_factory=time.time)
