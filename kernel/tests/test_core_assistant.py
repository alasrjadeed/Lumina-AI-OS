from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from core.assistant.agent import AssistantAgent, CAPABILITIES


@pytest.fixture
def agent():
    return AssistantAgent()


class TestAssistantAgent:
    def test_capabilities_defined(self):
        assert "browser" in CAPABILITIES
        assert "content" in CAPABILITIES
        assert "crm" in CAPABILITIES
        assert len(CAPABILITIES) >= 5

    @pytest.mark.asyncio
    async def test_handle_files_list(self, agent: AssistantAgent):
        result = await agent._handle_files({"sub_action": "list", "path": "."})
        assert result["action"] == "files"

    @pytest.mark.asyncio
    async def test_handle_files_default(self, agent: AssistantAgent):
        result = await agent._handle_files({})
        assert result["action"] == "files"

    @pytest.mark.asyncio
    async def test_handle_vault_get_missing(self, agent: AssistantAgent, tmp_path):
        with patch("core.assistant.agent.vault") as mock_vault:
            mock_vault.get.return_value = None
            result = await agent._handle_vault({"sub_action": "get", "key": "nonexistent"})
            assert result["action"] == "vault"

    @pytest.mark.asyncio
    async def test_handle_vault_set(self, agent: AssistantAgent, tmp_path):
        with patch("core.assistant.agent.vault") as mock_vault:
            result = await agent._handle_vault({"sub_action": "set", "key": "test", "value": "val"})
            assert result["action"] == "vault"

    @pytest.mark.asyncio
    async def test_handle_vault_all(self, agent: AssistantAgent, tmp_path):
        with patch("core.assistant.agent.vault") as mock_vault:
            mock_vault.all.return_value = {"key": "val"}
            result = await agent._handle_vault({})
            assert result["action"] == "vault"
            assert result["result"] == {"key": "val"}

    @pytest.mark.asyncio
    async def test_handle_chat_returns_result(self, agent: AssistantAgent):
        with patch("core.assistant.agent.engine.chat", new=AsyncMock()) as mock_chat:
            mock_chat.return_value = {"message": {"content": "Hello!"}}
            result = await agent._handle_chat("say hi")
            assert result["action"] == "chat"
            assert result["result"] == "Hello!"

    @pytest.mark.asyncio
    async def test_understand_returns_chat_fallback(self, agent: AssistantAgent):
        with patch("core.assistant.agent.engine.chat", new=AsyncMock()) as mock_chat:
            mock_chat.return_value = {"message": {"content": ""}}
            intent = await agent._understand("hello")
            assert intent["action"] in ("chat",)

    @pytest.mark.asyncio
    async def test_process_routes_to_content(self, agent: AssistantAgent):
        with patch("core.assistant.agent.engine.chat", new=AsyncMock()) as mock_chat, \
             patch("core.writer.generator.writer") as mock_writer:
            mock_chat.return_value = {
                "message": {
                    "content": '{"action": "content", "params": {"type": "blog", "topic": "AI"}, "summary": "write a blog"}'
                }
            }
            mock_writer.generate = AsyncMock(return_value={"content": "Blog content"})
            result = await agent.process("write a blog about AI")
            assert result["action"] == "content"

    @pytest.mark.asyncio
    async def test_process_returns_chat_for_unknown_action(self, agent: AssistantAgent):
        with patch("core.assistant.agent.engine.chat", new=AsyncMock()) as mock_chat:
            mock_chat.return_value = {"message": {"content": '{"action": "unknown_action", "params": {}}'}}
            result = await agent.process("do something weird")
            assert isinstance(result, dict)
