from __future__ import annotations

import pytest

from core.provider import AIEngine, AIProvider, OllamaProvider, OpenAIProvider, _ProviderSlot


class TestAIProvider:
    @pytest.mark.asyncio
    async def test_base_provider_raises(self):
        p = AIProvider()
        with pytest.raises(NotImplementedError):
            await p.chat([])

    def test_openai_chat_basic(self):
        p = AIProvider()
        data = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Hello!",
                    }
                }
            ]
        }
        result = p._openai_chat(data)
        assert result["message"]["content"] == "Hello!"
        assert "tool_calls" not in result["message"]

    def test_openai_chat_with_tool_calls(self):
        p = AIProvider()
        data = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "echo",
                                    "arguments": '{"message":"hi"}',
                                },
                            }
                        ],
                    }
                }
            ]
        }
        result = p._openai_chat(data)
        assert result["message"]["content"] is None
        assert len(result["message"]["tool_calls"]) == 1


class TestOllamaProvider:
    @pytest.mark.asyncio
    async def test_chat_uses_model_param(self):
        p = OllamaProvider()
        p.model = "test-model"
        with pytest.raises(Exception):
            await p.chat([{"role": "user", "content": "hi"}])

    @pytest.mark.asyncio
    async def test_check_health_offline(self):
        p = OllamaProvider()
        p.base_url = "http://localhost:1"
        result = await p.check_health()
        assert result is False


class TestAIEngine:
    def test_init_providers_ollama_only(self):
        engine = AIEngine()
        names = [p.name for p in engine.providers]
        assert "ollama" in names

    @pytest.mark.asyncio
    async def test_chat_all_fail(self):
        engine = AIEngine()
        engine._slots.clear()
        with pytest.raises(Exception, match="All providers failed"):
            await engine.chat([{"role": "user", "content": "hi"}])

    @pytest.mark.asyncio
    async def test_check_health_no_providers(self):
        engine = AIEngine()
        engine._slots.clear()
        result = await engine.check_health()
        assert result is False

    @pytest.mark.asyncio
    async def test_chat_propagates_tools(self):
        engine = AIEngine()
        engine._slots.clear()

        class TestProvider(OpenAIProvider):
            def __init__(self):
                self.name = "test"
                self.api_key = "test"
                self.base_url = "http://localhost:1"
                self.model = "test"

            async def chat(self, messages, tools=None, **kwargs):
                if tools:
                    return {"message": {"role": "assistant", "content": "used tools"}}
                return {"message": {"role": "assistant", "content": "no tools"}}

        engine._slots.append(_ProviderSlot(TestProvider()))
        result = await engine.chat([], tools=[{"type": "function", "function": {"name": "test"}}])
        assert result["message"]["content"] == "used tools"
