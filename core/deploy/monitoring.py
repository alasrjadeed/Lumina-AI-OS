from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class HealthStatus:
    service: str
    status: str = "unknown"
    latency_ms: float = 0.0
    last_check: float = field(default_factory=time.time)
    error: str = ""


@dataclass
class MetricPoint:
    name: str
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class Alert:
    name: str
    message: str
    severity: str = "warning"
    timestamp: float = field(default_factory=time.time)
    acknowledged: bool = False


class Monitoring:
    """Health checks, metrics collection, alerting, and status reporting."""

    def __init__(self, storage_path: str = "lumina_monitoring.json"):
        self.storage_path = storage_path
        self._health_status: dict[str, HealthStatus] = {}
        self._metrics: list[MetricPoint] = []
        self._alerts: list[Alert] = []
        self._alert_rules: list[dict] = []
        self._check_functions: dict[str, Callable] = {}
        self._max_metrics = 10000

    def register_check(self, name: str, check_fn: Callable) -> None:
        self._check_functions[name] = check_fn

    async def run_check(self, name: str) -> HealthStatus:
        fn = self._check_functions.get(name)
        if not fn:
            return HealthStatus(service=name, status="unknown", error="No check registered")
        start = time.time()
        try:
            if hasattr(fn, "__call__"):
                result = fn()
            status = "healthy" if result else "unhealthy"
            latency = (time.time() - start) * 1000
            hs = HealthStatus(service=name, status=status, latency_ms=latency)
        except Exception as e:
            hs = HealthStatus(service=name, status="unhealthy", error=str(e))
        self._health_status[name] = hs
        return hs

    async def run_all_checks(self) -> list[HealthStatus]:
        return [await self.run_check(name) for name in self._check_functions]

    def get_health(self, service: str = "") -> HealthStatus | dict[str, HealthStatus]:
        if service:
            return self._health_status.get(service, HealthStatus(service=service, status="unknown"))
        return dict(self._health_status)

    def record_metric(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        point = MetricPoint(name=name, value=value, labels=labels or {})
        self._metrics.append(point)
        if len(self._metrics) > self._max_metrics:
            self._metrics = self._metrics[-self._max_metrics:]
        self._evaluate_alerts(name, value)

    def query_metrics(self, name: str = "", limit: int = 100) -> list[MetricPoint]:
        if name:
            return [m for m in self._metrics if m.name == name][-limit:]
        return self._metrics[-limit:]

    def add_alert_rule(self, metric: str, operator: str, threshold: float,
                       severity: str = "warning", message: str = "") -> None:
        self._alert_rules.append({
            "metric": metric, "operator": operator, "threshold": threshold,
            "severity": severity, "message": message,
        })

    def _evaluate_alerts(self, metric_name: str, value: float) -> None:
        for rule in self._alert_rules:
            if rule["metric"] != metric_name:
                continue
            triggered = any([
                rule["operator"] == ">" and value > rule["threshold"],
                rule["operator"] == "<" and value < rule["threshold"],
                rule["operator"] == "==" and value == rule["threshold"],
            ])
            if triggered:
                self._alerts.append(Alert(
                    name=f"{metric_name}_{rule['operator']}_{rule['threshold']}",
                    message=rule["message"] or f"{metric_name} is {value}",
                    severity=rule["severity"],
                ))

    def get_alerts(self, severity: str = "", unacknowledged: bool = False) -> list[Alert]:
        results = list(self._alerts)
        if severity:
            results = [a for a in results if a.severity == severity]
        if unacknowledged:
            results = [a for a in results if not a.acknowledged]
        return results

    def acknowledge_alert(self, index: int) -> bool:
        if 0 <= index < len(self._alerts):
            self._alerts[index].acknowledged = True
            return True
        return False

    def summary(self) -> dict:
        health = list(self._health_status.values())
        return {
            "healthy_services": sum(1 for h in health if h.status == "healthy"),
            "unhealthy_services": sum(1 for h in health if h.status == "unhealthy"),
            "total_metrics": len(self._metrics),
            "active_alerts": len([a for a in self._alerts if not a.acknowledged]),
            "last_update": datetime.now().isoformat(),
        }

    def export_json(self, path: str = "monitoring_export.json") -> str:
        data = {
            "health": {k: {"service": v.service, "status": v.status,
                           "latency_ms": v.latency_ms, "last_check": v.last_check,
                           "error": v.error} for k, v in self._health_status.items()},
            "metrics": [{"name": m.name, "value": m.value, "labels": m.labels,
                         "timestamp": m.timestamp} for m in self._metrics[-500:]],
            "alerts": [{"name": a.name, "message": a.message, "severity": a.severity,
                        "timestamp": a.timestamp, "acknowledged": a.acknowledged}
                       for a in self._alerts[-100:]],
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return path
