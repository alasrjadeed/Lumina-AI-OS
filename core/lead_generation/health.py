from __future__ import annotations

from typing import Any

from core.log import log

from .models import ScraperStatus


class ScraperHealthCheck:
    def __init__(self, persistence=None):
        self._persistence = persistence
        self._max_consecutive_failures = 10

    def record_success(self, platform: str) -> None:
        if self._persistence:
            self._persistence.record_scraper_success(platform)

    def record_failure(self, platform: str, error: str = "", error_type: str = "") -> None:
        if self._persistence:
            self._persistence.record_scraper_failure(platform, error, error_type)

    def is_disabled(self, platform: str) -> bool:
        if not self._persistence:
            return False
        health = self._persistence.get_scraper_health()
        entry = health.get(platform)
        if entry and entry.status == "disabled":
            return True
        if entry and entry.consecutive_failures >= self._max_consecutive_failures:
            return True
        return False

    def get_status(self, platform: str) -> str:
        if not self._persistence:
            return "unknown"
        health = self._persistence.get_scraper_health()
        entry = health.get(platform)
        return entry.status if entry else "unknown"

    def get_all_health(self) -> dict[str, ScraperStatus]:
        if not self._persistence:
            return {}
        return self._persistence.get_scraper_health()

    def get_summary(self) -> dict[str, Any]:
        if not self._persistence:
            return {"healthy": 0, "failing": 0, "disabled": 0, "total": 0}
        health = self._persistence.get_scraper_health()
        healthy = sum(1 for h in health.values() if h.status == "healthy")
        failing = sum(1 for h in health.values() if h.status == "failing")
        disabled = sum(1 for h in health.values() if h.status == "disabled")
        return {
            "healthy": healthy,
            "failing": failing,
            "disabled": disabled,
            "total": len(health),
            "details": {
                k: {"status": v.status, "success_rate": self._success_rate(v)}
                for k, v in health.items()
            },
        }

    def validate_all(self) -> list[str]:
        if not self._persistence:
            return []
        health = self._persistence.get_scraper_health()
        disabled = [
            k for k, v in health.items()
            if v.consecutive_failures >= self._max_consecutive_failures
        ]
        log.info("Scraper validation: %d total, %d healthy, %d disabled",
                 len(health), len(health) - len(disabled), len(disabled))
        return disabled

    @staticmethod
    def _success_rate(status: ScraperStatus) -> float:
        total = status.success_count + status.failure_count
        if total == 0:
            return 100.0
        return round(status.success_count / total * 100, 1)
