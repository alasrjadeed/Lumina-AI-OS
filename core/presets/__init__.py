"""Agent presets — pre-configured agent profiles for common use cases.

Inspired by OpenJarvis preset system (morning-digest, deep-research,
code-assistant, scheduled-monitor, chat-simple).
"""

from core.presets.registry import AgentPreset, PresetRegistry

__all__ = ["AgentPreset", "PresetRegistry"]
