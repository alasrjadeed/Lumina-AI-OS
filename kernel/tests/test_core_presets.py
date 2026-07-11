from __future__ import annotations

from core.presets.registry import AgentPreset, PresetRegistry


class TestPresetRegistry:
    def test_default_presets_loaded(self):
        presets = registry.list()
        assert len(presets) == 12

    def test_get_preset(self):
        preset = registry.get("morning-digest")
        assert preset is not None
        assert preset.label == "Morning Digest"
        assert preset.category == "productivity"

    def test_list_by_category(self):
        dev_presets = registry.list(category="development")
        assert len(dev_presets) >= 1
        assert all(p.category == "development" for p in dev_presets)

    def test_categories(self):
        cats = registry.categories()
        assert "development" in cats
        assert "productivity" in cats
        assert "general" in cats

    def test_register_custom_preset(self):
        preset = AgentPreset(name="test-agent", label="Test", description="A test preset")
        registry.register(preset)
        assert registry.get("test-agent") is not None


registry = PresetRegistry()
