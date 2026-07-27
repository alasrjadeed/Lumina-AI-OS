from __future__ import annotations

import asyncio
import hashlib
import time
from typing import Any

import httpx

from core.log import log
from .models import PlatformInfo

APIFY_BASE = "https://api.apify.com/v2"

APIFY_ACTOR_MAP: dict[str, PlatformInfo] = {
    "google_maps": PlatformInfo(
        key="google_maps", name="Google Maps",
        category="core", scraper_type="apify",
        apify_actor="compass~crawler-google-places",
    ),
    "instagram": PlatformInfo(
        key="instagram", name="Instagram",
        category="social", scraper_type="python",
        apify_actor="apify~instagram-scraper",
    ),
    "tiktok": PlatformInfo(
        key="tiktok", name="TikTok",
        category="social", scraper_type="python",
        apify_actor="clockworks~tiktok-scraper",
    ),
    "youtube": PlatformInfo(
        key="youtube", name="YouTube",
        category="social", scraper_type="python",
        apify_actor="streamers~youtube-scraper",
    ),
    "facebook": PlatformInfo(
        key="facebook", name="Facebook",
        category="social", scraper_type="python",
        apify_actor="apify~facebook-posts-scraper",
    ),
    "twitter": PlatformInfo(
        key="twitter", name="Twitter/X",
        category="social", scraper_type="http",
        apify_actor="apidojo~tweet-scraper",
    ),
    "google_search": PlatformInfo(
        key="google_search", name="Google Search",
        category="core", scraper_type="apify",
        apify_actor="apify~google-search-scraper",
    ),
    "google_reviews": PlatformInfo(
        key="google_reviews", name="Google Reviews",
        category="core", scraper_type="apify",
        apify_actor="compass~Google-Maps-Reviews-Scraper",
    ),
    "ecommerce": PlatformInfo(
        key="ecommerce", name="E-Commerce",
        category="core", scraper_type="apify",
        apify_actor="apify~e-commerce-scraping-tool",
    ),
    "website_content": PlatformInfo(
        key="website_content", name="Website Content",
        category="core", scraper_type="apify",
        apify_actor="vaclavrut~website-content-crawler",
    ),
    "linkedin": PlatformInfo(
        key="linkedin", name="LinkedIn",
        category="social", scraper_type="python",
        apify_actor="",
        requires_auth=True,
    ),
}


class ApifyClient:
    def __init__(self, tokens: list[str] | None = None):
        self._tokens = tokens or []
        self._token_index = 0
        self._last_used: dict[str, float] = {}
        self._client: httpx.AsyncClient | None = None

    def set_tokens(self, tokens: list[str]) -> None:
        self._tokens = [t for t in tokens if t]
        self._token_index = 0

    @property
    def active_token(self) -> str | None:
        if not self._tokens:
            return None
        return self._tokens[self._token_index % len(self._tokens)]

    def rotate_token(self) -> None:
        if len(self._tokens) > 1:
            self._token_index = (self._token_index + 1) % len(self._tokens)
            log.info("Rotated to Apify token %d/%d", self._token_index + 1, len(self._tokens))

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0),
                base_url=APIFY_BASE,
            )
        return self._client

    async def run_actor(
        self,
        actor_id: str,
        run_input: dict[str, Any],
        wait: bool = True,
        max_retries: int = 2,
    ) -> dict[str, Any]:
        token = self.active_token
        if not token:
            return {"error": "No Apify token configured", "data": []}

        client = await self._get_client()
        last_error = ""

        for attempt in range(max_retries + 1):
            try:
                log.info("Apify: running actor %s (attempt %d/%d)", actor_id, attempt + 1, max_retries + 1)
                resp = await client.post(
                    f"/acts/{actor_id}/runs",
                    params={"token": token, "waitForFinish": 60 if wait else 0},
                    json=run_input,
                )
                if resp.status_code == 429:
                    self.rotate_token()
                    await asyncio.sleep(2)
                    continue

                resp.raise_for_status()
                run_data = resp.json()
                run_id = run_data.get("data", {}).get("id", "")

                if wait and run_id:
                    results = await self._wait_for_run(client, token, actor_id, run_id)
                    return {"run_id": run_id, "data": results}

                return {"run_id": run_id, "data": []}

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    self.rotate_token()
                    await asyncio.sleep(2 ** attempt)
                last_error = str(e)
            except Exception as e:
                last_error = str(e)
                await asyncio.sleep(1)

        return {"error": last_error, "data": []}

    async def _wait_for_run(
        self,
        client: httpx.AsyncClient,
        token: str,
        actor_id: str,
        run_id: str,
        max_wait: float = 90.0,
    ) -> list[dict[str, Any]]:
        start = time.time()
        while time.time() - start < max_wait:
            try:
                resp = await client.get(
                    f"/acts/{actor_id}/runs/{run_id}",
                    params={"token": token},
                )
                resp.raise_for_status()
                run = resp.json()
                status = run.get("data", {}).get("status", "")

                if status in ("SUCCEEDED",):
                    return await self._get_dataset(client, token, run.get("data", {}).get("defaultDatasetId", ""))
                elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
                    log.warning("Apify run %s ended with status: %s", run_id, status)
                    return []

                await asyncio.sleep(3)

            except Exception as e:
                log.warning("Apify poll error: %s", e)
                await asyncio.sleep(5)

        log.warning("Apify run %s timed out after %.0fs", run_id, max_wait)
        return []

    async def _get_dataset(
        self, client: httpx.AsyncClient, token: str, dataset_id: str
    ) -> list[dict[str, Any]]:
        if not dataset_id:
            return []
        try:
            resp = await client.get(
                f"/datasets/{dataset_id}/items",
                params={"token": token, "format": "json", "limit": 200},
            )
            resp.raise_for_status()
            return resp.json() if isinstance(resp.json(), list) else []
        except Exception as e:
            log.warning("Apify dataset error: %s", e)
            return []

    async def fetch_google_maps(
        self, keyword: str, location: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        actor = APIFY_ACTOR_MAP["google_maps"].apify_actor
        result = await self.run_actor(actor, {
            "searchStringsArray": [f"{keyword} in {location}"],
            "maxCrawledPlaces": limit,
            "language": "en",
            "maxImages": 0,
            "maxReviews": 0,
            "includeWebResults": True,
        })
        return result.get("data", [])

    async def fetch_google_search(
        self, keyword: str, location: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        actor = APIFY_ACTOR_MAP["google_search"].apify_actor
        result = await self.run_actor(actor, {
            "queries": f'"{keyword}" "{location}" business contact',
            "maxPagesPerQuery": 1,
            "resultsPerPage": limit,
            "countryCode": "bh",
        })
        return result.get("data", [])

    async def fetch_google_reviews(
        self, keyword: str, location: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        actor = APIFY_ACTOR_MAP["google_reviews"].apify_actor
        result = await self.run_actor(actor, {
            "searchStringsArray": [f"{keyword} {location}"],
            "maxReviews": limit,
        })
        return result.get("data", [])

    async def fetch_ecommerce(
        self, keyword: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        actor = APIFY_ACTOR_MAP["ecommerce"].apify_actor
        result = await self.run_actor(actor, {
            "searchPhrase": keyword,
            "maxItems": limit,
        })
        return result.get("data", [])

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    @staticmethod
    def compute_hash(value: str) -> str:
        if not value:
            return ""
        return hashlib.sha256(value.strip().lower().encode()).hexdigest()
