from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from typing import Any

from core.log import log

SCRIPTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "scripts", "scrapers",
)


class PythonScraperGateway:
    @staticmethod
    async def scrape(
        platform: str,
        keyword: str,
        location: str = "",
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        js_platforms = {"instagram", "tiktok", "facebook", "linkedin", "youtube"}
        python_platforms = {
            "expatriates", "opensooq", "olx", "dubizzle", "haraj", "bayut",
            "arabiantalks", "dcciinfo", "abcgcc", "bahrainyellow", "bayt",
            "gulftalent", "gumtree",
        }

        if platform in js_platforms:
            return await PythonScraperGateway._run_playwright(platform, keyword, location, limit)
        elif platform in python_platforms:
            return await PythonScraperGateway._run_fast(platform, keyword, location, limit)
        else:
            log.info("No Python scraper for platform: %s, falling back to Apify/AI", platform)
            return []

    @staticmethod
    async def _run_playwright(
        platform: str, keyword: str, location: str, limit: int
    ) -> list[dict[str, Any]]:
        script = os.path.join(SCRIPTS_DIR, "playwright_scraper.py")
        if not os.path.exists(script):
            log.warning("Playwright scraper not found: %s", script)
            return []
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, script, platform, keyword, location, str(limit),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60.0)
            if proc.returncode != 0:
                err = stderr.decode(errors="replace")[:500]
                log.warning("Playwright scraper failed for %s: %s", platform, err)
                return []
            return json.loads(stdout.decode() or "[]")
        except asyncio.TimeoutError:
            log.warning("Playwright scraper timeout for %s", platform)
            return []
        except Exception as e:
            log.warning("Playwright scraper error for %s: %s", platform, e)
            return []

    @staticmethod
    async def _run_fast(
        platform: str, keyword: str, location: str, limit: int
    ) -> list[dict[str, Any]]:
        script = os.path.join(SCRIPTS_DIR, "fast_scraper.py")
        if not os.path.exists(script):
            log.warning("Fast scraper not found: %s", script)
            return []
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, script, platform, keyword, location, str(limit),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30.0)
            if proc.returncode != 0:
                err = stderr.decode(errors="replace")[:500]
                log.warning("Fast scraper failed for %s: %s", platform, err)
                return []
            return json.loads(stdout.decode() or "[]")
        except asyncio.TimeoutError:
            log.warning("Fast scraper timeout for %s", platform)
            return []
        except Exception as e:
            log.warning("Fast scraper error for %s: %s", platform, e)
            return []
