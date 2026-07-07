from __future__ import annotations

import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CommandCategory(Enum):
    NAVIGATION = "navigation"
    QUERY = "query"
    ACTION = "action"
    SETTINGS = "settings"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class VoiceCommand:
    text: str
    intent: str = ""
    category: CommandCategory = CommandCategory.UNKNOWN
    confidence: float = 0.0
    entities: dict[str, str] = field(default_factory=dict)
    raw_text: str = ""
    timestamp: float = field(default_factory=time.time)


CommandHandler = Callable[[VoiceCommand], Any]


@dataclass
class IntentPattern:
    intent: str
    category: CommandCategory
    patterns: list[str]
    handler: CommandHandler | None = None


class VoiceCommandRouter:
    """Parse and route voice commands to handlers."""

    def __init__(self):
        self._intents: list[IntentPattern] = []
        self._fallback_handler: CommandHandler | None = None
        self._history: list[VoiceCommand] = []

    def register(
        self,
        intent: str,
        category: CommandCategory,
        patterns: list[str],
        handler: CommandHandler | None = None,
    ) -> None:
        self._intents.append(IntentPattern(
            intent=intent,
            category=category,
            patterns=patterns,
            handler=handler,
        ))

    def set_fallback(self, handler: CommandHandler) -> None:
        self._fallback_handler = handler

    def parse(self, text: str) -> VoiceCommand:
        lower = text.lower().strip()
        best_intent: str | None = None
        best_category = CommandCategory.UNKNOWN
        best_confidence = 0.0
        best_entities: dict[str, str] = {}

        for intent_def in self._intents:
            for pattern in intent_def.patterns:
                compiled = re.compile(pattern, re.IGNORECASE)
                match = compiled.search(lower)
                if match:
                    confidence = min(1.0, len(match.group()) / max(len(lower), 1) + 0.3)
                    if confidence > best_confidence:
                        best_intent = intent_def.intent
                        best_category = intent_def.category
                        best_confidence = confidence
                        best_entities = match.groupdict()

        cmd = VoiceCommand(
            text=lower,
            intent=best_intent or "unknown",
            category=best_category,
            confidence=best_confidence,
            entities=best_entities,
            raw_text=text,
        )
        self._history.append(cmd)
        return cmd

    def route(self, text: str) -> Any:
        cmd = self.parse(text)
        for intent_def in self._intents:
            if intent_def.intent == cmd.intent and intent_def.handler:
                return intent_def.handler(cmd)
        if self._fallback_handler:
            return self._fallback_handler(cmd)
        return None

    def get_history(self, limit: int = 10) -> list[VoiceCommand]:
        return self._history[-limit:]

    def clear_history(self) -> None:
        self._history.clear()

    @staticmethod
    def default_router() -> VoiceCommandRouter:
        router = VoiceCommandRouter()
        router.register("search", CommandCategory.QUERY, [
            r"(?:search|find|look up|query)\s+(?:for\s+)?(?P<query>.+)",
            r"(?:what|who|when|where|why|how)\s+(?:is|are|was|were|does|do|can)\s+(?P<query>.+)",
        ])
        router.register("navigate", CommandCategory.NAVIGATION, [
            r"(?:go to|open|navigate to|show)\s+(?P<page>.+)",
            r"(?:take me to|switch to)\s+(?P<page>.+)",
        ])
        router.register("create", CommandCategory.ACTION, [
            r"(?:create|make|new|build)\s+(?P<type>\w+)\s+(?:called|named\s+)?(?P<name>.+)",
        ])
        router.register("remind", CommandCategory.ACTION, [
            r"(?:remind|set reminder|remember)\s+(?:me\s+)?(?:to\s+)?(?P<task>.+)",
        ])
        router.register("settings", CommandCategory.SETTINGS, [
            r"(?:change|set|update|adjust)\s+(?P<setting>\w+)\s+(?:to\s+)?(?P<value>.+)",
        ])
        router.register("stop", CommandCategory.SYSTEM, [
            r"^(?:stop|exit|quit|shutdown|goodbye|bye)\s*$",
        ])
        router.register("help", CommandCategory.SYSTEM, [
            r"^(?:help|what can you do|commands|options)\s*$",
        ])
        return router
