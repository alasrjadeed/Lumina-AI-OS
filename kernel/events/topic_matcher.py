"""
Lumina AI
Topic Matcher

Supports wildcard topic matching.
"""

from __future__ import annotations


class TopicMatcher:
    """
    Match event names against subscription topics.

    Supported patterns (in precedence order):

    *                     Match everything
    **                    Match everything (explicit globstar)
    plugin.loaded         Exact match
    browser.*             Single-level wildcard (browser.X, not browser.X.Y)
    browser.**            Multi-level wildcard (browser, browser.X, browser.X.Y)
    """

    @staticmethod
    def matches(
        subscription: str,
        topic: str,
    ) -> bool:
        if subscription in ("*", "**"):
            return True

        if subscription == topic:
            return True

        if subscription.endswith(".**"):
            prefix = subscription[:-3]
            return topic == prefix or topic.startswith(prefix + ".")

        if subscription.endswith(".*"):
            prefix = subscription[:-2]
            if topic == prefix:
                return True
            if topic.startswith(prefix + "."):
                suffix = topic[len(prefix) + 1 :]
                return "." not in suffix
            return False

        return False
