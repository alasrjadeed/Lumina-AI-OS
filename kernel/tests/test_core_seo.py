from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from core.seo.analytics import SEOAnalytics


@pytest.fixture
def seo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SEOAnalytics:
    seo_path = str(tmp_path / "seo_data.json")
    monkeypatch.setattr("core.seo.analytics.SEO_FILE", seo_path)
    return SEOAnalytics()


class TestSEOAnalytics:
    def test_add_site(self, seo: SEOAnalytics):
        site = seo.add_site("https://example.com", "Example")
        assert site["url"] == "https://example.com"
        assert site["name"] == "Example"

    def test_add_site_default_name(self, seo: SEOAnalytics):
        site = seo.add_site("https://test.com")
        assert site["name"] == "https://test.com"

    def test_list_sites_empty(self, seo: SEOAnalytics):
        assert seo.list_sites() == []

    def test_list_sites_with_data(self, seo: SEOAnalytics):
        seo.add_site("https://a.com")
        seo.add_site("https://b.com")
        assert len(seo.list_sites()) == 2

    def test_add_keyword(self, seo: SEOAnalytics):
        kw = seo.add_keyword("python", volume=1200, difficulty=45)
        assert kw["keyword"] == "python"
        assert kw["volume"] == 1200
        assert kw["difficulty"] == 45

    def test_add_keyword_with_site(self, seo: SEOAnalytics):
        site = seo.add_site("https://example.com")
        kw = seo.add_keyword("test", site_id=site["id"])
        assert kw["site_id"] == site["id"]

    @pytest.mark.asyncio
    async def test_analyze_page_returns_error_on_failure(self, seo: SEOAnalytics):
        with patch("core.seo.analytics.engine.chat", new=AsyncMock()) as mock:
            mock.side_effect = ValueError("No LLM")
            result = await seo.analyze_page("<html></html>", "https://test.com")
            assert "error" in result

    @pytest.mark.asyncio
    async def test_generate_meta_returns_empty_on_failure(self, seo: SEOAnalytics):
        with patch("core.seo.analytics.engine.chat", new=AsyncMock()) as mock:
            mock.side_effect = ValueError("No LLM")
            result = await seo.generate_meta("some content", "test keyword")
            assert result["title"] == ""

    def test_get_audit_history_empty(self, seo: SEOAnalytics):
        assert seo.get_audit_history() == []

    def test_get_audit_history_limit(self, seo: SEOAnalytics):
        assert seo.get_audit_history(limit=5) == []

    def test_persistence(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        seo_path = str(tmp_path / "seo_persist.json")
        monkeypatch.setattr("core.seo.analytics.SEO_FILE", seo_path)
        s1 = SEOAnalytics()
        s1.add_site("https://persist.com")
        s2 = SEOAnalytics()
        urls = [site["url"] for site in s2.list_sites()]
        assert "https://persist.com" in urls
