from __future__ import annotations

from .models import CountryInfo, PlatformInfo, COUNTRY_CLASSIFIEDS_MAP, COUNTRY_METADATA, GCC_COUNTRIES

CLASSIFIED_PLATFORMS: dict[str, PlatformInfo] = {
    "expatriates": PlatformInfo(key="expatriates", name="Expatriates.com", category="classifieds", scraper_type="python"),
    "opensooq": PlatformInfo(key="opensooq", name="OpenSooq", category="classifieds", scraper_type="python"),
    "olx": PlatformInfo(key="olx", name="OLX", category="classifieds", scraper_type="python"),
    "dubizzle": PlatformInfo(key="dubizzle", name="Dubizzle", category="classifieds", scraper_type="python"),
    "haraj": PlatformInfo(key="haraj", name="Haraj", category="classifieds", scraper_type="python"),
    "bayut": PlatformInfo(key="bayut", name="Bayut", category="classifieds", scraper_type="python"),
    "arabiantalks": PlatformInfo(key="arabiantalks", name="ArabianTalks", category="classifieds", scraper_type="python"),
    "dcciinfo": PlatformInfo(key="dcciinfo", name="DCCI Info", category="classifieds", scraper_type="python"),
    "abcgcc": PlatformInfo(key="abcgcc", name="ABC GCC", category="classifieds", scraper_type="python"),
    "bahrainyellow": PlatformInfo(key="bahrainyellow", name="Bahrain Yellow Pages", category="classifieds", scraper_type="python"),
    "bayt": PlatformInfo(key="bayt", name="Bayt.com", category="jobs", scraper_type="python"),
    "gulftalent": PlatformInfo(key="gulftalent", name="GulfTalent", category="jobs", scraper_type="python"),
    "gumtree": PlatformInfo(key="gumtree", name="Gumtree", category="classifieds", scraper_type="python"),
    "craigslist": PlatformInfo(key="craigslist", name="Craigslist", category="classifieds", scraper_type="http"),
}

GLOBAL_SCRAPERS: dict[str, PlatformInfo] = {
    "linkedin": PlatformInfo(key="linkedin", name="LinkedIn", category="social", scraper_type="python", requires_auth=True),
    "meetup": PlatformInfo(key="meetup", name="Meetup", category="social", scraper_type="http"),
    "reddit": PlatformInfo(key="reddit", name="Reddit", category="social", scraper_type="http"),
    "pinterest": PlatformInfo(key="pinterest", name="Pinterest", category="social", scraper_type="http"),
    "yelp": PlatformInfo(key="yelp", name="Yelp", category="reviews", scraper_type="http"),
    "tripadvisor": PlatformInfo(key="tripadvisor", name="TripAdvisor", category="reviews", scraper_type="http"),
    "foursquare": PlatformInfo(key="foursquare", name="Foursquare", category="reviews", scraper_type="http"),
    "justdial": PlatformInfo(key="justdial", name="JustDial", category="directory", scraper_type="http"),
    "sulekha": PlatformInfo(key="sulekha", name="Sulekha", category="directory", scraper_type="http"),
    "thumbtack": PlatformInfo(key="thumbtack", name="Thumbtack", category="services", scraper_type="http"),
    "vivastreet": PlatformInfo(key="vivastreet", name="VivaStreet", category="classifieds", scraper_type="http"),
    "nextdoor": PlatformInfo(key="nextdoor", name="Nextdoor", category="social", scraper_type="http"),
    "nooncareers": PlatformInfo(key="nooncareers", name="Noon Careers", category="jobs", scraper_type="http"),
}


class PlatformRegistry:
    def __init__(self):
        from .apify_client import APIFY_ACTOR_MAP
        self._apify = APIFY_ACTOR_MAP
        self._classifieds = CLASSIFIED_PLATFORMS
        self._global = GLOBAL_SCRAPERS

    def all_platforms(self) -> list[PlatformInfo]:
        platforms: list[PlatformInfo] = []
        platforms.extend(self._apify.values())
        for key, info in self._classifieds.items():
            if key not in {p.key for p in platforms}:
                platforms.append(info)
        for key, info in self._global.items():
            if key not in {p.key for p in platforms}:
                platforms.append(info)
        return sorted(platforms, key=lambda p: p.key)

    def get(self, key: str) -> PlatformInfo | None:
        return self._apify.get(key) or self._classifieds.get(key) or self._global.get(key)

    def by_category(self, category: str) -> list[PlatformInfo]:
        return [p for p in self.all_platforms() if p.category == category]

    def by_scraper_type(self, scraper_type: str) -> list[PlatformInfo]:
        return [p for p in self.all_platforms() if p.scraper_type == scraper_type]

    def for_country(self, country_code: str) -> list[str]:
        code = country_code.upper() if len(country_code) <= 2 else self._find_code(country_code)
        return COUNTRY_CLASSIFIEDS_MAP.get(code, [])

    def countries(self) -> list[CountryInfo]:
        return [COUNTRY_METADATA[c] for c in GCC_COUNTRIES]

    @staticmethod
    def _find_code(name: str) -> str:
        name_lower = name.lower()
        for code, info in COUNTRY_METADATA.items():
            if info.name.lower() == name_lower or code.lower() == name_lower:
                return code
        return "BH"
