"""
Lumina AI
Topic Matcher

Supports wildcard topic matching.
"""

from __future__ import annotations


class TopicMatcher:
    """
    Match event names against subscription topics.

    Supported:

    *

    kernel.*

    browser.*

    browser.tab.*

    plugin.loaded
    """

    @staticmethod
    def matches(
        subscription: str,
        topic: str,
    ) -> bool:
        if subscription == "*":
            return True

        if subscription == topic:
            return True

        if subscription.endswith(".*"):
            prefix = subscription[:-2]
            return (
                topic == prefix
                or topic.startswith(prefix + ".")
            )

        return False
