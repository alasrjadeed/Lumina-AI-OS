from __future__ import annotations

import csv
import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime

from core.desktop.plugin_manager import PluginMetadata
from core.log import log


@dataclass
class ReportMetric:
    label: str
    value: float
    unit: str = ""
    change: float = 0.0


@dataclass
class ReportSection:
    title: str
    metrics: list[ReportMetric] = field(default_factory=list)
    data: list[dict] = field(default_factory=list)
    chart_type: str = "table"


@dataclass
class Report:
    title: str
    sections: list[ReportSection] = field(default_factory=list)
    generated: float = field(default_factory=time.time)
    format: str = "json"


metadata = PluginMetadata(
    name="Reporting",
    version="1.0.0",
    description="Report generation, data visualization, scheduled reports, and multi-format export",
    author="Lumina",
    hooks=["report_generated", "report_exported", "report_scheduled"],
)

_reports: list[Report] = []
_storage_path = "reporting_plugin_data.json"


def on_load() -> None:
    _load_data()
    log.info("Reporting plugin loaded")


def on_unload() -> None:
    _save_data()


def on_enable() -> None:
    log.info("Reporting enabled")


def on_disable() -> None:
    log.info("Reporting disabled")


def _load_data() -> None:
    global _reports
    if os.path.exists(_storage_path):
        try:
            with open(_storage_path) as f:
                data = json.load(f)
            _reports = []
            for r in data.get("reports", []):
                sections = [ReportSection(**s) for s in r.get("sections", [])]
                _reports.append(Report(title=r["title"], sections=sections,
                                       generated=r.get("generated", 0)))
        except Exception:
            pass


def _save_data() -> None:
    with open(_storage_path, "w") as f:
        json.dump({
            "reports": [{"title": r.title,
                         "sections": [{"title": s.title,
                                       "metrics": [{"label": m.label, "value": m.value,
                                                     "unit": m.unit, "change": m.change}
                                                    for m in s.metrics],
                                       "chart_type": s.chart_type}
                                      for s in r.sections],
                         "generated": r.generated}
                        for r in _reports[-20:]],
        }, f, indent=2)


def create_report(title: str) -> Report:
    report = Report(title=title, sections=[])
    _reports.append(report)
    _save_data()
    return report


def add_section(
    report_title: str, section_title: str, chart_type: str = "table"
) -> ReportSection | None:
    for r in _reports:
        if r.title == report_title:
            section = ReportSection(title=section_title, chart_type=chart_type)
            r.sections.append(section)
            _save_data()
            return section
    return None


def add_metric(report_title: str, section_title: str, label: str, value: float,
               unit: str = "", change: float = 0.0) -> bool:
    for r in _reports:
        if r.title == report_title:
            for s in r.sections:
                if s.title == section_title:
                    s.metrics.append(
                        ReportMetric(label=label, value=value, unit=unit, change=change)
                    )
                    _save_data()
                    return True
    return False


def add_table_data(report_title: str, section_title: str, data: list[dict]) -> bool:
    for r in _reports:
        if r.title == report_title:
            for s in r.sections:
                if s.title == section_title:
                    s.data.extend(data)
                    _save_data()
                    return True
    return False


def list_reports(limit: int = 20) -> list[Report]:
    return _reports[-limit:]


def get_report(title: str) -> Report | None:
    for r in _reports:
        if r.title == title:
            return r
    return None


def export_csv(report_title: str, section_title: str, path: str = "") -> str:
    report = get_report(report_title)
    if not report:
        return ""
    section = next((s for s in report.sections if s.title == section_title), None)
    if not section:
        return ""
    export_path = path or f"{report_title.replace(' ', '_')}_{section_title.replace(' ', '_')}.csv"
    if not section.data:
        with open(export_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Metric", "Value", "Unit", "Change"])
            for m in section.metrics:
                writer.writerow([m.label, m.value, m.unit, m.change])
    else:
        with open(export_path, "w", newline="") as f:
            if section.data:
                writer = csv.DictWriter(f, fieldnames=section.data[0].keys())
                writer.writeheader()
                writer.writerows(section.data)
    log.info("CSV exported: %s", export_path)
    return export_path


def export_json(report_title: str, path: str = "") -> str:
    report = get_report(report_title)
    if not report:
        return ""
    export_path = path or f"{report_title.replace(' ', '_')}.json"
    with open(export_path, "w") as f:
        json.dump({
            "title": report.title,
            "generated": report.generated,
            "sections": [{"title": s.title, "chart_type": s.chart_type,
                          "metrics": [{"label": m.label, "value": m.value,
                                       "unit": m.unit, "change": m.change} for m in s.metrics],
                          "data": s.data} for s in report.sections],
        }, f, indent=2)
    log.info("JSON exported: %s", export_path)
    return export_path


def export_html(report_title: str, path: str = "") -> str:
    report = get_report(report_title)
    if not report:
        return ""
    export_path = path or f"{report_title.replace(' ', '_')}.html"
    html = [_html_header(report.title)]
    for section in report.sections:
        html.append(f"<h2>{section.title}</h2>")
        if section.metrics:
            html.append('<table border="1" cellpadding="6" style="border-collapse:collapse">')
            html.append("<tr><th>Metric</th><th>Value</th><th>Unit</th><th>Change</th></tr>")
            for m in section.metrics:
                change_str = f"{m.change:+.1f}%" if m.change else "-"
                html.append(f"<tr><td>{m.label}</td><td>{m.value}</td><td>{m.unit}</td><td>{change_str}</td></tr>")
            html.append("</table>")
        if section.data:
            html.append('<table border="1" cellpadding="6" style="border-collapse:collapse">')
            if section.data:
                html.append("<tr>" + "".join(f"<th>{k}</th>" for k in section.data[0]) + "</tr>")
                html.extend(
                    "<tr>" + "".join(f"<td>{v}</td>" for v in row.values()) + "</tr>"
                    for row in section.data
                )
            html.append("</table>")
    html.append("</body></html>")
    with open(export_path, "w") as f:
        f.write("\n".join(html))
    log.info("HTML exported: %s", export_path)
    return export_path


def _html_header(title: str) -> str:
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{title}</title>
<style>body{{font-family:sans-serif;margin:20px;color:#333}}
h1{{color:#1a1a2e}}h2{{color:#16213e;margin-top:24px}}
table{{width:100%;margin:12px 0}}th{{background:#1a1a2e;color:#fff;padding:8px}}
td{{padding:8px;border-bottom:1px solid #ddd}}</style></head><body>
<h1>{title}</h1><p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>"""


def generate_summary_report(data_sources: list[dict]) -> Report:
    report = create_report("Summary Report")
    section = add_section("Summary Report", "Overview", "metrics")
    if section:
        total = len(data_sources)
        avg = sum(d.get("value", 0) for d in data_sources) / total if total else 0
        section.metrics.append(ReportMetric(label="Total Items", value=total))
        section.metrics.append(ReportMetric(label="Average Value", value=avg))
    section2 = add_section("Summary Report", "Data Table", "table")
    if section2:
        section2.data = data_sources
    return report
