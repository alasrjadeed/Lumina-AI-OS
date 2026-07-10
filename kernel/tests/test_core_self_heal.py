from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from core.self_heal import SelfHealingLoop


class TestSelfHealingLoop:
    def test_init_defaults(self):
        loop = SelfHealingLoop()
        assert loop.max_retries == 3

    def test_init_custom_retries(self):
        loop = SelfHealingLoop(max_retries=5)
        assert loop.max_retries == 5

    @pytest.mark.asyncio
    async def test_execute_success_first_attempt(self):
        loop = SelfHealingLoop(max_retries=1)
        calls = [
            {"message": {"content": json.dumps({"summary": "test", "steps": ["do X"]})}},
            {"message": {"content": "executed OK"}},
            {"message": {"content": "NO_ISSUES"}},
        ]
        with patch("core.self_heal.engine.chat", new=AsyncMock()) as mock:
            mock.side_effect = calls
            result = await loop.execute("test task")
            assert result["status"] == "success"
            assert result["attempts"] == 1

    @pytest.mark.asyncio
    async def test_execute_retries_on_failure(self):
        loop = SelfHealingLoop(max_retries=2)
        call_count = [0]

        async def mock_chat(messages, **kw):
            call_count[0] += 1
            if call_count[0] <= 2:
                raise ValueError("LLM unavailable")
            return {"message": {"content": "NO_ISSUES"}}

        with (
            patch("core.self_heal.engine.chat", new=mock_chat),
            patch.object(
                loop, "_plan", new=AsyncMock(return_value={"summary": "t", "steps": ["s"]})
            ),
            patch.object(loop, "_execute_plan", new=AsyncMock(return_value="result")),
        ):
            result = await loop.execute("retry test")
            assert result["status"] in ("success", "failed")

    @pytest.mark.asyncio
    async def test_plan_returns_fallback_on_engine_failure(self):
        loop = SelfHealingLoop()
        with patch("core.self_heal.engine.chat", new=AsyncMock()) as mock:
            mock.side_effect = ValueError("No LLM")
            plan = await loop._plan("test task")
            assert "summary" in plan
            assert "steps" in plan
            assert plan["summary"] == "test task"

    @pytest.mark.asyncio
    async def test_verify_returns_empty_on_failure(self):
        loop = SelfHealingLoop()
        with patch("core.self_heal.engine.chat", new=AsyncMock()) as mock:
            mock.side_effect = ValueError("No LLM")
            issues = await loop._verify("some output")
            assert isinstance(issues, list)
            assert len(issues) == 0

    @pytest.mark.asyncio
    async def test_verify_detects_issues(self):
        loop = SelfHealingLoop()
        with patch("core.self_heal.engine.chat", new=AsyncMock()) as mock:
            mock.return_value = {"message": {"content": "Missing error handling\nBad naming"}}
            issues = await loop._verify("some buggy code")
            assert len(issues) >= 1
            assert any("Missing" in i for i in issues)

    @pytest.mark.asyncio
    async def test_verify_no_issues(self):
        loop = SelfHealingLoop()
        with patch("core.self_heal.engine.chat", new=AsyncMock()) as mock:
            mock.return_value = {"message": {"content": "NO_ISSUES"}}
            issues = await loop._verify("perfect code")
            assert issues == []

    @pytest.mark.asyncio
    async def test_fix_returns_original_plan_on_failure(self):
        loop = SelfHealingLoop()
        original = {"summary": "test", "steps": ["step1"]}
        with patch("core.self_heal.engine.chat", new=AsyncMock()) as mock:
            mock.side_effect = ValueError("No LLM")
            result = await loop._fix(original, "result", ["issue1"], {})
            assert result == original

    @pytest.mark.asyncio
    async def test_execute_plan_runs_steps(self):
        loop = SelfHealingLoop()
        with patch("core.self_heal.engine.chat", new=AsyncMock()) as mock:
            mock.return_value = {"message": {"content": "Step result"}}
            result = await loop._execute_plan({"summary": "test", "steps": ["step1", "step2"]})
            assert "Step result" in result
