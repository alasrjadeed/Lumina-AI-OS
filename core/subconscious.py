"""Subconscious Loop — background agent that diffs your world and pushes proactive insights."""

from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Callable

from core.log import log

_SUBCONSCIOUS_DIR = os.path.expanduser("~/.lumina/subconscious")
_CHECK_INTERVAL = 300
_BRIEFING_INTERVAL = 43200


class SubconsciousState:
    def __init__(self):
        self._seen_episodes: set[str] = set()
        self._last_briefing_time: float = 0.0
        self._load()

    def _path(self) -> str:
        os.makedirs(_SUBCONSCIOUS_DIR, exist_ok=True)
        return os.path.join(_SUBCONSCIOUS_DIR, "state.json")

    def _load(self) -> None:
        path = self._path()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                self._seen_episodes = set(data.get("seen_episodes", []))
                self._last_briefing_time = data.get("last_briefing_time", 0.0)
            except Exception:
                pass

    def _save(self) -> None:
        with open(self._path(), "w") as f:
            json.dump({
                "seen_episodes": list(self._seen_episodes)[-1000:],
                "last_briefing_time": self._last_briefing_time,
            }, f, indent=2)

    def is_new_episode(self, episode_id: str) -> bool:
        return episode_id not in self._seen_episodes

    def mark_seen(self, episode_id: str) -> None:
        self._seen_episodes.add(episode_id)
        if len(self._seen_episodes) > 2000:
            self._seen_episodes = set(list(self._seen_episodes)[-1000:])
        self._save()

    def should_brief(self) -> bool:
        return (time.time() - self._last_briefing_time) > _BRIEFING_INTERVAL

    def mark_briefed(self) -> None:
        self._last_briefing_time = time.time()
        self._save()


_state = SubconsciousState()


class Insight:
    def __init__(self, title: str, body: str, category: str = "general", priority: int = 0):
        self.title = title
        self.body = body
        self.category = category
        self.priority = priority
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "body": self.body,
            "category": self.category,
            "priority": self.priority,
            "timestamp": self.timestamp,
        }


_insight_hooks: list[Callable[[], list[Insight]]] = []


def register_insight_hook(hook: Callable[[], list[Insight]]) -> None:
    _insight_hooks.append(hook)


async def subconscious_loop(
    on_insight: Callable[[Insight], Any] | None = None,
):
    """Background loop that periodically checks for new insights and generates briefings."""
    log.info("Subconscious loop started (check every %ds, briefing every %ds)", _CHECK_INTERVAL, _BRIEFING_INTERVAL)

    while True:
        try:
            all_insights: list[Insight] = []
            for hook in _insight_hooks:
                try:
                    insights = hook()
                    all_insights.extend(insights)
                except Exception as e:
                    log.warning("Subconscious hook error: %s", e)

            for insight in all_insights:
                if on_insight:
                    try:
                        if asyncio.iscoroutinefunction(on_insight):
                            await on_insight(insight)
                        else:
                            on_insight(insight)
                    except Exception as e:
                        log.warning("Subconscious on_insight error: %s", e)

            if _state.should_brief():
                briefing = _generate_briefing(all_insights)
                if briefing and on_insight:
                    try:
                        if asyncio.iscoroutinefunction(on_insight):
                            await on_insight(briefing)
                        else:
                            on_insight(briefing)
                    except Exception:
                        pass
                _state.mark_briefed()

            _state._save()

        except asyncio.CancelledError:
            log.info("Subconscious loop cancelled")
            break
        except Exception as e:
            log.warning("Subconscious loop error: %s", e)

        await asyncio.sleep(_CHECK_INTERVAL)


def _generate_briefing(recent_insights: list[Insight]) -> Insight:
    high_priority = [i for i in recent_insights if i.priority >= 1]
    body_parts = ["## Subconscious Briefing", ""]
    body_parts.append(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    body_parts.append("")

    if high_priority:
        body_parts.append("### Notable")
        for i in high_priority[:5]:
            body_parts.append(f"- **{i.title}**: {i.body[:200]}")

    body_parts.append("")
    body_parts.append(f"*{len(recent_insights)} recent signals analyzed*")

    return Insight(
        title="Morning Briefing",
        body="\n".join(body_parts),
        category="briefing",
        priority=2,
    )
