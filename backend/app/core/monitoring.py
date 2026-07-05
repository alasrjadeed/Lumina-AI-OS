import time
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class SystemMonitor:
    def __init__(self):
        self._start_time = time.time()
        self._request_count = 0
        self._error_count = 0
        self._endpoint_stats: Dict[str, Dict] = {}

    def record_request(self, method: str, path: str, status: int, duration: float):
        self._request_count += 1
        if status >= 500:
            self._error_count += 1
        key = f"{method} {path}"
        if key not in self._endpoint_stats:
            self._endpoint_stats[key] = {"count": 0, "errors": 0, "total_duration": 0.0}
        self._endpoint_stats[key]["count"] += 1
        self._endpoint_stats[key]["total_duration"] += duration
        if status >= 500:
            self._endpoint_stats[key]["errors"] += 1

    def get_stats(self) -> Dict[str, Any]:
        uptime = time.time() - self._start_time
        return {
            "uptime_seconds": uptime,
            "uptime_formatted": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m",
            "total_requests": self._request_count,
            "total_errors": self._error_count,
            "error_rate": round(self._error_count / max(self._request_count, 1) * 100, 2),
            "requests_per_second": round(self._request_count / max(uptime, 1), 2),
            "endpoints": {
                k: {
                    "count": v["count"],
                    "avg_duration_ms": round(v["total_duration"] / max(v["count"], 1) * 1000, 2),
                    "errors": v["errors"],
                }
                for k, v in sorted(self._endpoint_stats.items(), key=lambda x: x[1]["count"], reverse=True)
            },
        }


monitor = SystemMonitor()
