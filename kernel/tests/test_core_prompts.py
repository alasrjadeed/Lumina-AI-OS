from __future__ import annotations

import pytest

from core.prompts.manager import PromptManager


class TestPromptManager:
    def test_default_templates_loaded(self):
        pm = PromptManager()
        assert "chat" in pm.list_templates()
        assert "code" in pm.list_templates()

    def test_get_template(self):
        pm = PromptManager()
        tmpl = pm.get("chat")
        assert tmpl is not None
        assert "user" in tmpl

    def test_get_nonexistent(self):
        pm = PromptManager()
        assert pm.get("nonexistent") is None

    def test_render_chat(self):
        pm = PromptManager()
        msgs = pm.render("chat", {"message": "hello world"})
        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"
        assert "hello world" in msgs[1]["content"]

    def test_render_code(self):
        pm = PromptManager()
        msgs = pm.render("code", {"language": "python", "description": "sort list"})
        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert "python" in msgs[0]["content"]

    def test_render_unknown_raises(self):
        pm = PromptManager()
        with pytest.raises(ValueError, match="Unknown template"):
            pm.render("nonexistent", {})

    def test_register_new(self):
        pm = PromptManager()
        pm.register("custom", {"system": "You are custom.", "user": "Do: {task}"})
        assert "custom" in pm.list_templates()
        msgs = pm.render("custom", {"task": "test"})
        assert "test" in msgs[1]["content"]

    def test_versioning(self):
        pm = PromptManager()
        v1 = pm.get_version("chat")
        pm.register("chat", {"system": "v2", "user": "v2"})
        v2 = pm.get_version("chat")
        assert v2 > v1

    def test_get_by_version(self):
        pm = PromptManager()
        v1 = pm.get("chat", version=1)
        pm.register("chat", {"system": "v2", "user": "v2"})
        v2 = pm.get("chat", version=2)
        assert v1 is not None
        assert v2 is not None
        assert v1 != v2

    def test_get_history(self):
        pm = PromptManager()
        history = pm.get_history("chat")
        assert len(history) >= 1
        assert history[0]["version"] == 1
