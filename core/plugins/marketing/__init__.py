from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum

from core.desktop.plugin_manager import PluginMetadata
from core.log import log


class ChannelType(Enum):
    EMAIL = "email"
    SOCIAL = "social"
    SMS = "sms"
    WEB = "web"
    ADS = "ads"


@dataclass
class ContentItem:
    title: str
    content: str
    channel: str = "web"
    scheduled: float = 0.0
    status: str = "draft"
    tags: list[str] = field(default_factory=list)


@dataclass
class MarketingCampaign:
    name: str
    channel: ChannelType = ChannelType.EMAIL
    budget: float = 0.0
    spent: float = 0.0
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    status: str = "draft"
    start_date: float = 0.0
    end_date: float = 0.0


metadata = PluginMetadata(
    name="Marketing",
    version="1.0.0",
    description="Campaign management, multi-channel marketing, content calendar, and analytics",
    author="Lumina",
    hooks=["campaign_launched", "content_published", "campaign_analyzed"],
)

_campaigns: dict[str, MarketingCampaign] = {}
_content_calendar: list[ContentItem] = []
_storage_path = "marketing_plugin_data.json"


def on_load() -> None:
    _load_data()
    log.info("Marketing plugin loaded")


def on_unload() -> None:
    _save_data()


def on_enable() -> None:
    log.info("Marketing enabled")


def on_disable() -> None:
    log.info("Marketing disabled")


def _load_data() -> None:
    global _campaigns, _content_calendar
    if not os.path.exists(_storage_path):
        return
    try:
        with open(_storage_path) as f:
            data = json.load(f)
        _campaigns = {k: MarketingCampaign(**v) for k, v in data.get("campaigns", {}).items()}
        _content_calendar = [ContentItem(**c) for c in data.get("content", [])]
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        log.error("Failed to load marketing data: %s", e)


def _save_data() -> None:
    with open(_storage_path, "w") as f:
        json.dump({
            "campaigns": {k: {"name": c.name, "channel": c.channel.value, "budget": c.budget,
                              "spent": c.spent, "impressions": c.impressions, "clicks": c.clicks,
                              "conversions": c.conversions, "status": c.status,
                              "start_date": c.start_date, "end_date": c.end_date}
                          for k, c in _campaigns.items()},
            "content": [{"title": c.title, "content": c.content, "channel": c.channel,
                         "scheduled": c.scheduled, "status": c.status, "tags": c.tags}
                        for c in _content_calendar],
        }, f, indent=2)


def create_campaign(name: str, channel: str = "email", budget: float = 0.0) -> MarketingCampaign:
    campaign = MarketingCampaign(
        name=name, channel=ChannelType(channel), budget=budget,
        start_date=time.time(),
    )
    _campaigns[name] = campaign
    _save_data()
    return campaign


def get_campaign(name: str) -> MarketingCampaign | None:
    return _campaigns.get(name)


def list_campaigns(status: str = "") -> list[MarketingCampaign]:
    if status:
        return [c for c in _campaigns.values() if c.status == status]
    return list(_campaigns.values())


def launch_campaign(name: str) -> bool:
    campaign = _campaigns.get(name)
    if campaign and campaign.status == "draft":
        campaign.status = "active"
        _save_data()
        return True
    return False


def pause_campaign(name: str) -> bool:
    campaign = _campaigns.get(name)
    if campaign and campaign.status == "active":
        campaign.status = "paused"
        _save_data()
        return True
    return False


def complete_campaign(name: str) -> bool:
    campaign = _campaigns.get(name)
    if campaign:
        campaign.status = "completed"
        campaign.end_date = time.time()
        _save_data()
        return True
    return False


def track_impression(name: str, count: int = 1) -> None:
    campaign = _campaigns.get(name)
    if campaign:
        campaign.impressions += count
        _save_data()


def track_click(name: str, count: int = 1) -> None:
    campaign = _campaigns.get(name)
    if campaign:
        campaign.clicks += count
        _save_data()


def track_conversion(name: str, count: int = 1) -> None:
    campaign = _campaigns.get(name)
    if campaign:
        campaign.conversions += count
        _save_data()


def get_campaign_metrics(name: str) -> dict:
    campaign = _campaigns.get(name)
    if not campaign:
        return {}
    ctr = (campaign.clicks / campaign.impressions * 100) if campaign.impressions else 0.0
    cvr = (campaign.conversions / campaign.clicks * 100) if campaign.clicks else 0.0
    roas = ((campaign.conversions * 50) / campaign.spent) if campaign.spent else 0.0
    return {
        "impressions": campaign.impressions,
        "clicks": campaign.clicks,
        "conversions": campaign.conversions,
        "ctr": round(ctr, 2),
        "conversion_rate": round(cvr, 2),
        "spent": campaign.spent,
        "budget": campaign.budget,
        "roas": round(roas, 2),
    }


def schedule_content(title: str, content: str, channel: str = "web",
                     scheduled_time: float = 0.0, tags: list[str] | None = None) -> ContentItem:
    item = ContentItem(title=title, content=content, channel=channel,
                       scheduled=scheduled_time or time.time(), tags=tags or [])
    _content_calendar.append(item)
    _save_data()
    return item


def publish_content(title: str) -> bool:
    for item in _content_calendar:
        if item.title == title and item.status == "draft":
            item.status = "published"
            _save_data()
            return True
    return False


def get_content_calendar(status: str = "", channel: str = "") -> list[ContentItem]:
    results = list(_content_calendar)
    if status:
        results = [c for c in results if c.status == status]
    if channel:
        results = [c for c in results if c.channel == channel]
    return sorted(results, key=lambda c: c.scheduled)


def get_summary() -> dict:
    total_budget = sum(c.budget for c in _campaigns.values())
    total_spent = sum(c.spent for c in _campaigns.values())
    total_impressions = sum(c.impressions for c in _campaigns.values())
    total_clicks = sum(c.clicks for c in _campaigns.values())
    total_conversions = sum(c.conversions for c in _campaigns.values())
    return {
        "active_campaigns": sum(1 for c in _campaigns.values() if c.status == "active"),
        "total_campaigns": len(_campaigns),
        "total_budget": total_budget,
        "total_spent": total_spent,
        "total_impressions": total_impressions,
        "total_clicks": total_clicks,
        "total_conversions": total_conversions,
        "content_scheduled": sum(1 for c in _content_calendar if c.status == "draft"),
        "content_published": sum(1 for c in _content_calendar if c.status == "published"),
    }
