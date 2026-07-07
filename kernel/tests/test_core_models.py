from __future__ import annotations

from core.models.router import ModelCapability, ModelRouter

MODELS = [
    ModelCapability(
        name="ollama", provider="ollama", context_window=4096,
        supports_tools=True, cost_per_1k_input=0, cost_per_1k_output=0,
        capabilities=["code", "general", "chat"], priority=0,
    ),
    ModelCapability(
        name="gpt-4o-mini", provider="openai", context_window=16000,
        supports_tools=True, cost_per_1k_input=0.15, cost_per_1k_output=0.6,
        capabilities=["code", "reasoning", "general", "chat"], priority=5,
    ),
    ModelCapability(
        name="claude-sonnet", provider="openrouter", context_window=32000,
        supports_tools=True, cost_per_1k_input=3, cost_per_1k_output=15,
        capabilities=["reasoning", "creative", "code"], priority=10,
    ),
    ModelCapability(
        name="gemini-flash", provider="gemini", context_window=32000,
        supports_tools=False, cost_per_1k_input=0, cost_per_1k_output=0,
        capabilities=["general", "chat"], priority=3,
    ),
]


class TestModelRouter:
    def test_add_and_list(self):
        router = ModelRouter()
        router.add_model(MODELS[0])
        assert len(router.list_models()) == 1

    def test_remove_model(self):
        router = ModelRouter()
        router.add_model(MODELS[0])
        router.remove_model("ollama")
        assert len(router.list_models()) == 0

    def test_route_picks_free_for_code(self):
        router = ModelRouter(models=MODELS)
        model = router.route("write python code", prefer_free=True)  # noqa: E501
        assert model is not None
        assert model.cost_per_1k_input == 0

    def test_route_picks_capable_for_reasoning(self):
        router = ModelRouter(models=MODELS)
        model = router.route("perform deep reasoning analysis on the data and research findings", prefer_free=False)  # noqa: E501
        assert model is not None
        assert "reasoning" in model.capabilities

    def test_route_falls_back_to_chat(self):
        router = ModelRouter(models=MODELS)
        model = router.route("hello how are you")  # noqa: E501
        assert model is not None

    def test_empty_models_returns_none(self):
        router = ModelRouter()
        assert router.route("anything") is None  # noqa: E501

    def test_detect_capability_code(self):
        router = ModelRouter()
        caps = router._detect_capability("write python code to sort data")
        assert "code" in caps

    def test_detect_capability_creative(self):
        router = ModelRouter()
        caps = router._detect_capability("write a creative story about AI")
        assert "creative" in caps

    def test_detect_capability_fallback(self):
        router = ModelRouter()
        caps = router._detect_capability("what is the weather")
        assert caps == ["chat"]
