"""Analytics Engine — cross-module metrics, dashboards, and forecasting."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field

ANALYTICS_DIR = os.path.expanduser("~/.lumina/analytics")


@dataclass
class Metric:
    name: str
    value: float
    unit: str = ""
    category: str = "general"
    timestamp: float = 0.0
    tags: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "category": self.category,
            "timestamp": self.timestamp,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Metric:
        return cls(
            name=d["name"],
            value=d["value"],
            unit=d.get("unit", ""),
            category=d.get("category", "general"),
            timestamp=d.get("timestamp", 0),
            tags=d.get("tags", {}),
        )


class AnalyticsEngine:
    """Collect, store, and analyze metrics across all Lumina modules."""

    def __init__(self):
        self._metrics: list[Metric] = []
        self._snapshots: dict[str, dict] = {}
        self._forecasts: dict[str, list[float]] = {}
        self._load()

    def _path(self) -> str:
        os.makedirs(ANALYTICS_DIR, exist_ok=True)
        return os.path.join(ANALYTICS_DIR, "metrics.json")

    def _snap_path(self) -> str:
        os.makedirs(ANALYTICS_DIR, exist_ok=True)
        return os.path.join(ANALYTICS_DIR, "snapshots.json")

    def _load(self):
        path = self._path()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                self._metrics = [Metric.from_dict(d) for d in data[-5000:]]
            except Exception:
                pass

        spath = self._snap_path()
        if os.path.exists(spath):
            try:
                with open(spath) as f:
                    self._snapshots = json.load(f)
            except Exception:
                pass

    def _save(self):
        with open(self._path(), "w") as f:
            json.dump([m.to_dict() for m in self._metrics[-5000:]], f, indent=2)

    def track(
        self,
        name: str,
        value: float,
        unit: str = "",
        category: str = "general",
        tags: dict[str, str] | None = None,
    ):
        self._metrics.append(
            Metric(
                name=name,
                value=value,
                unit=unit,
                category=category,
                timestamp=time.time(),
                tags=tags or {},
            )
        )
        if len(self._metrics) > 1000 and len(self._metrics) % 100 == 0:
            self._save()

    def snapshot(self, category: str, data: dict):
        self._snapshots[category] = {
            "data": data,
            "timestamp": time.time(),
        }
        with open(self._snap_path(), "w") as f:
            json.dump(self._snapshots, f, indent=2)

    def get_snapshot(self, category: str) -> dict | None:
        return self._snapshots.get(category)

    def query(
        self, name: str = "", category: str = "", since: float = 0, limit: int = 100
    ) -> list[Metric]:
        results = list(self._metrics)
        if name:
            results = [m for m in results if m.name == name]
        if category:
            results = [m for m in results if m.category == category]
        if since:
            results = [m for m in results if m.timestamp >= since]
        return sorted(results, key=lambda m: m.timestamp, reverse=True)[:limit]

    def aggregate(self, name: str, period: str = "day") -> dict:
        matching = [m for m in self._metrics if m.name == name]
        if not matching:
            return {"name": name, "count": 0}

        now = time.time()
        period_sec = {
            "hour": 3600,
            "day": 86400,
            "week": 604800,
            "month": 2592000,
        }.get(period, 86400)

        recent = [m for m in matching if now - m.timestamp <= period_sec]
        values = [m.value for m in recent]

        return {
            "name": name,
            "count": len(recent),
            "sum": sum(values) if values else 0,
            "avg": sum(values) / len(values) if values else 0,
            "min": min(values) if values else 0,
            "max": max(values) if values else 0,
            "latest": recent[-1].value if recent else 0,
            "period": period,
            "unit": recent[-1].unit if recent else "",
        }

    def trends(self, name: str, buckets: int = 24) -> list[dict]:
        matching = [m for m in self._metrics if m.name == name]
        if not matching:
            return []

        matching.sort(key=lambda m: m.timestamp)
        t_min = min(m.timestamp for m in matching)
        t_max = max(m.timestamp for m in matching) + 1
        bucket_size = (t_max - t_min) / buckets

        result = []
        for i in range(buckets):
            start = t_min + i * bucket_size
            end = start + bucket_size
            bucket_vals = [m.value for m in matching if start <= m.timestamp < end]
            result.append(
                {
                    "bucket": i,
                    "timestamp": start,
                    "value": sum(bucket_vals) / len(bucket_vals) if bucket_vals else 0,
                    "count": len(bucket_vals),
                }
            )
        return result

    def forecast(self, name: str, ahead: int = 7) -> list[dict]:
        trend = self.trends(name, buckets=ahead * 2)
        if not trend or len(trend) < 4:
            return []

        values = [b["value"] for b in trend if b["count"] > 0]
        if len(values) < 2:
            return []

        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        slope = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values)) / max(
            sum((i - x_mean) ** 2 for i in range(n)), 1
        )

        last_ts = max(b["timestamp"] for b in trend)
        bucket_size = (
            max(b["timestamp"] for b in trend if b["count"] > 0)
            - min(b["timestamp"] for b in trend if b["count"] > 0)
        ) / max(len(values) - 1, 1)

        result = []
        for i in range(1, ahead + 1):
            pred = max(0, y_mean + slope * (n + i - 1 - x_mean))
            result.append(
                {
                    "day": i,
                    "timestamp": last_ts + i * bucket_size,
                    "predicted": round(pred, 2),
                    "lower": round(pred * 0.8, 2),
                    "upper": round(pred * 1.2, 2),
                }
            )
        return result

    def dashboard(self) -> dict:
        now = time.time()
        day_ago = now - 86400
        week_ago = now - 604800

        recent = [m for m in self._metrics if m.timestamp >= day_ago]
        weekly = [m for m in self._metrics if m.timestamp >= week_ago]

        by_category: dict[str, int] = {}
        by_name: dict[str, float] = {}
        for m in recent:
            by_category[m.category] = by_category.get(m.category, 0) + 1
            if m.name not in by_name or m.timestamp > by_name.get(f"{m.name}_ts", 0):
                by_name[m.name] = m.value
                by_name[f"{m.name}_ts"] = m.timestamp

        return {
            "period": "24h",
            "total_metrics_today": len(recent),
            "total_metrics_week": len(weekly),
            "categories": by_category,
            "latest_values": {k: v for k, v in by_name.items() if not k.endswith("_ts")},
            "snapshots": list(self._snapshots.keys()),
            "generated_at": time.time(),
        }

    def generate_report(self, categories: list[str] | None = None) -> str:
        now = time.time()
        day_ago = now - 86400

        cats = categories or list({m.category for m in self._metrics if m.timestamp >= day_ago})

        sections = ["# Analytics Report\n"]
        sections.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M')}\n")

        for cat in cats:
            cat_metrics = [m for m in self._metrics if m.category == cat and m.timestamp >= day_ago]
            if not cat_metrics:
                continue
            sections.append(f"\n## {cat.title()}")
            by_name: dict[str, list[float]] = {}
            for m in cat_metrics:
                by_name.setdefault(m.name, []).append(m.value)
            for name, vals in by_name.items():
                sections.append(
                    f"- **{name}**: avg={sum(vals) / len(vals):.1f}, "
                    f"min={min(vals):.1f}, max={max(vals):.1f}, count={len(vals)}"
                )

        return "\n".join(sections)

    def reset(self):
        self._metrics.clear()
        self._snapshots.clear()
        self._save()
        if os.path.exists(self._snap_path()):
            os.remove(self._snap_path())

    def stats(self) -> dict:
        return {
            "total_metrics": len(self._metrics),
            "categories": len({m.category for m in self._metrics}),
            "unique_names": len({m.name for m in self._metrics}),
            "snapshots": len(self._snapshots),
            "oldest_ts": min(m.timestamp for m in self._metrics) if self._metrics else 0,
            "newest_ts": max(m.timestamp for m in self._metrics) if self._metrics else 0,
        }


analytics = AnalyticsEngine()
