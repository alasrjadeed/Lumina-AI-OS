from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime

from core.browser.automation import browser
from core.desktop.plugin_manager import PluginMetadata
from core.log import log
from core.seo.analytics import SEOAnalytics


@dataclass
class AuditResult:
    url: str
    score: float = 0.0
    issues: list[dict] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "score": self.score,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "timestamp": self.timestamp,
        }


metadata = PluginMetadata(
    name="SEO Suite",
    version="1.0.0",
    description="SEO analysis, keyword tracking, site audits, and competitor research",
    author="Lumina",
    hooks=["seo_audit", "keyword_analyzed", "report_generated"],
)

seo = SEOAnalytics()
_sites: list[str] = []
_keywords: list[str] = []
_audit_history: list[AuditResult] = []


def on_load() -> None:
    log.info("SEO Suite plugin loaded")


def on_unload() -> None:
    _sites.clear()
    _keywords.clear()
    _audit_history.clear()


def on_enable() -> None:
    log.info("SEO Suite enabled")


def on_disable() -> None:
    log.info("SEO Suite disabled")


def add_site(url: str, name: str = "") -> dict:
    result = seo.add_site(url, name)
    _sites.append(url)
    return result


def list_sites() -> list[dict]:
    return seo.list_sites()


def track_keyword(keyword: str, site_url: str = "") -> dict:
    result = seo.add_keyword(keyword, site_url)
    if keyword not in _keywords:
        _keywords.append(keyword)
    return result


def list_keywords() -> list[dict]:
    return list(seo._data.get("keywords", []))


async def run_audit(url: str) -> AuditResult:
    try:
        await browser.navigate(url)
        assert browser._page is not None
        title = (
            await browser.get_text("title") if await browser._page.query_selector("title") else ""
        )
        meta_desc = await browser._page.evaluate(
            "document.querySelector('meta[name=\"description\"]')?.content || ''",
        )
        headings = await browser._page.evaluate("""() =>
            ['h1','h2','h3'].map(t => document.querySelectorAll(t).length)
        """)
        images = await browser._page.evaluate(
            "Array.from(document.querySelectorAll('img')).filter(i => !i.alt).length",
        )
        await browser._page.evaluate(
            "document.querySelectorAll('a[href]').length",
        )
        await browser._page.evaluate(
            "performance.getEntriesByType('navigation')[0]?.domContentLoadedEventEnd || 0",
        )
        issues = []
        suggestions = []
        if not title:
            issues.append({"type": "missing_title", "severity": "high"})
            suggestions.append("Add a descriptive <title> tag")
        if not meta_desc:
            issues.append({"type": "missing_meta_description", "severity": "high"})
            suggestions.append("Add a meta description tag")
        if headings and headings[0] == 0:
            issues.append({"type": "missing_h1", "severity": "high"})
            suggestions.append("Add an H1 heading")
        if images > 0:
            issues.append({"type": "missing_alt_text", "severity": "medium", "count": images})
            suggestions.append(f"Add alt text to {images} images")
        score = max(0, 100 - len(issues) * 20)
        result = AuditResult(url=url, score=score, issues=issues, suggestions=suggestions)
        _audit_history.append(result)
        return result
    except Exception as e:
        log.error("SEO audit failed for %s: %s", url, e)
        return AuditResult(
            url=url,
            score=0,
            issues=[{"type": "audit_error", "severity": "high", "detail": str(e)}],
        )


def get_audit_history(limit: int = 10) -> list[dict]:
    return [a.to_dict() for a in _audit_history[-limit:]]


def analyze_competitor(url: str, keywords: list[str]) -> dict:
    return {
        "url": url,
        "keywords_found": [k for k in keywords if k.lower() in url.lower()],
        "keyword_count": len(keywords),
    }


def generate_report() -> dict:
    return {
        "sites": len(_sites),
        "keywords": len(_keywords),
        "audits": len(_audit_history),
        "average_score": (
            sum(a.score for a in _audit_history) / len(_audit_history) if _audit_history else 0
        ),
        "generated_at": datetime.now().isoformat(),
    }
