from __future__ import annotations

from core.context.manager import ContextManager


class TestContextManager:
    def test_add_and_count(self):
        cm = ContextManager()
        cm.add("user", "hello")
        cm.add("assistant", "hi there")
        assert cm.count() == 2

    def test_get_messages(self):
        cm = ContextManager()
        cm.add("user", "hello")
        msgs = cm.get_messages()
        assert len(msgs) == 1
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == "hello"

    def test_last(self):
        cm = ContextManager()
        cm.add("user", "first")
        cm.add("user", "second")
        last = cm.last(1)
        assert last[0]["content"] == "second"

    def test_clear(self):
        cm = ContextManager()
        cm.add("user", "hello")
        cm.clear()
        assert cm.count() == 0

    def test_metadata(self):
        cm = ContextManager()
        cm.set_metadata("session_id", "abc123")
        assert cm.get_metadata("session_id") == "abc123"
        assert cm.get_metadata("nonexistent", "default") == "default"

    def test_window(self):
        cm = ContextManager()
        for i in range(5):
            cm.add("user", f"msg{i}")
        window = cm.window(1, 3)
        assert len(window) == 2
        assert window[0]["content"] == "msg1"

    def test_add_message(self):
        cm = ContextManager()
        cm.add_message({"role": "user", "content": "hello"})
        assert cm.count() == 1

    def test_trim_respects_budget(self):
        cm = ContextManager(max_tokens=50, reserve_tokens=10)
        for i in range(20):
            cm.add("user", "hello world this is a long message " * 5)
        assert cm.count() <= 5
