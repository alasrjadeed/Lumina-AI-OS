import json
import os
import re
from datetime import datetime

from core.log import log
from core.provider import engine

_BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEO_FILE = os.path.join(_BASE, "seo_data.json")


class SEOAnalytics:
    def __init__(self):
        self._data = self._load()

    def _load(self) -> dict:
        if os.path.exists(SEO_FILE):
            with open(SEO_FILE) as f:
                return json.load(f)
        return {"sites": [], "keywords": [], "audits": []}

    def _save(self):
        with open(SEO_FILE, "w") as f:
            json.dump(self._data, f, indent=2)

    def add_site(self, url: str, name: str = "") -> dict:
        site = {
            "id": str(len(self._data["sites"]) + 1),
            "url": url,
            "name": name or url,
            "created_at": self._now_iso(),
        }
        self._data["sites"].append(site)
        self._save()
        log.info("SEO site added: %s", url)
        return site

    def _now_iso(self) -> str:
        return datetime.now().isoformat()

    def list_sites(self) -> list[dict]:
        return self._data["sites"]

    async def analyze_page(self, html: str, url: str = "") -> dict:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an SEO analyst. Analyze this HTML page and return JSON with: "
                    "title, meta_description, headings (h1-h6 count), img_alt_issues, "
                    "word_count, readability_score (1-10), suggestions."
                ),
            },
            {"role": "user", "content": f"URL: {url}\n\nHTML:\n{html[:4000]}"},
        ]
        try:
            resp = await engine.chat(messages)
            text = resp["message"]["content"]
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                data = json.loads(match.group())
                data["url"] = url
                data["timestamp"] = self._now_iso()
                self._data["audits"].append(data)
                self._save()
                return data
        except Exception as e:
            log.error("SEO analysis failed: %s", e)
        return {"url": url, "error": "Analysis failed"}

    async def generate_meta(self, page_content: str, focus_keyword: str = "") -> dict:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an SEO content strategist. Generate optimized meta tags "
                    "for this content. Return JSON with: title (max 60 chars), "
                    "meta_description (max 160 chars), focus_keywords, slug."
                ),
            },
            {
                "role": "user",
                "content": (f"Focus keyword: {focus_keyword}\n\nContent:\n{page_content[:3000]}"),
            },
        ]
        try:
            resp = await engine.chat(messages)
            text = resp["message"]["content"]
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        return {"title": "", "meta_description": "", "focus_keywords": [], "slug": ""}

    async def audit_site(self, url: str, html: str) -> dict:
        return await self.analyze_page(html, url)

    def get_audit_history(self, limit: int = 20) -> list[dict]:
        return self._data["audits"][-limit:]

    def add_keyword(
        self, keyword: str, site_id: str = "", volume: int = 0, difficulty: int = 0
    ) -> dict:
        kw = {
            "id": str(len(self._data["keywords"]) + 1),
            "keyword": keyword,
            "site_id": site_id,
            "volume": volume,
            "difficulty": difficulty,
            "created_at": self._now_iso(),
        }
        self._data["keywords"].append(kw)
        self._save()
        return kw


seo = SEOAnalytics()
