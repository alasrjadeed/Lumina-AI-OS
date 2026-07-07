from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.crm.pipeline import CRMPipeline, DealStage
from core.desktop.plugin_manager import PluginMetadata
from core.log import log


@dataclass
class DealAnalytics:
    total_deals: int = 0
    won_deals: int = 0
    lost_deals: int = 0
    total_value: float = 0.0
    won_value: float = 0.0
    conversion_rate: float = 0.0
    avg_deal_value: float = 0.0


metadata = PluginMetadata(
    name="CRM",
    version="1.0.0",
    description="Contact management, deal tracking, pipeline analytics, and activity logging",
    author="Lumina",
    hooks=["deal_created", "deal_stage_changed", "contact_added"],
)

pipeline = CRMPipeline()


def on_load() -> None:
    log.info("CRM plugin loaded")


def on_unload() -> None:
    pass


def on_enable() -> None:
    log.info("CRM enabled")


def on_disable() -> None:
    log.info("CRM disabled")


def add_contact(
    name: str, email: str = "", phone: str = "", company: str = "", **extra: Any
) -> dict:
    return pipeline.add_contact(name, email, phone, company, **extra)


def list_contacts() -> list[dict]:
    return pipeline.list_contacts()


def search_contacts(query: str) -> list[dict]:
    q = query.lower()
    return [c for c in pipeline.list_contacts()
            if q in c.get("name", "").lower() or q in c.get("email", "").lower()]


def add_deal(title: str, value: float, contact_id: str = "", stage: str = "lead") -> dict:
    stage_enum = DealStage(stage) if isinstance(stage, str) else stage
    return pipeline.add_deal(title, value, contact_id, stage_enum)


def update_deal_stage(deal_id: str, stage: str) -> dict | None:
    stage_enum = DealStage(stage) if isinstance(stage, str) else stage
    return pipeline.update_deal_stage(deal_id, stage_enum)


def list_deals(stage: str = "") -> list[dict]:
    return pipeline.list_deals(stage)


def get_deal_analytics() -> DealAnalytics:
    deals = pipeline.list_deals()
    won = [d for d in deals if d.get("stage") == "closed_won"]
    lost = [d for d in deals if d.get("stage") == "closed_lost"]
    total_value = sum(d.get("value", 0) for d in deals)
    won_value = sum(d.get("value", 0) for d in won)
    return DealAnalytics(
        total_deals=len(deals),
        won_deals=len(won),
        lost_deals=len(lost),
        total_value=total_value,
        won_value=won_value,
        conversion_rate=(len(won) / len(deals) * 100) if deals else 0.0,
        avg_deal_value=(won_value / len(won)) if won else 0.0,
    )


def log_activity(contact_id: str, activity_type: str, description: str) -> dict:
    return pipeline.add_activity(contact_id, activity_type, description)


def get_pipeline_summary() -> list[dict]:
    stages = []
    for stage in DealStage:
        deals = pipeline.list_deals(stage.value)
        total = sum(d.get("value", 0) for d in deals)
        stages.append({"stage": stage.value, "count": len(deals), "total_value": total})
    return stages
