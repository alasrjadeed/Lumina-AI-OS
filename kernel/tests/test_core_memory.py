from __future__ import annotations

import time

import pytest

from core.memory.consolidation import ConsolidationEngine
from core.memory.engine import MemoryEngine
from core.memory.episodic import Episode, EpisodicMemory
from core.memory.semantic import Fact, SemanticMemory
from core.memory.store import MemoryStore
from core.memory.working import WorkingMemory


class TestWorkingMemory:
    def test_set_and_get(self):
        wm = WorkingMemory(default_ttl=60.0)
        wm.set("key1", "value1")
        assert wm.get("key1") == "value1"

    def test_get_default(self):
        wm = WorkingMemory()
        assert wm.get("nonexistent", default="fallback") == "fallback"

    def test_ttl_expiry(self):
        wm = WorkingMemory(default_ttl=0.0)
        wm.set("key", "val")
        time.sleep(0.01)
        assert wm.get("key") is None

    def test_task_isolation(self):
        wm = WorkingMemory()
        wm.set("key", "task1_val", task_id="task1")
        wm.set("key", "task2_val", task_id="task2")
        assert wm.get("key", task_id="task1") == "task1_val"
        assert wm.get("key", task_id="task2") == "task2_val"

    def test_clear_task(self):
        wm = WorkingMemory()
        wm.set("a", "1", task_id="t1")
        wm.set("b", "2", task_id="t2")
        wm.clear_task("t1")
        assert wm.get("a", task_id="t1") is None
        assert wm.get("b", task_id="t2") == "2"

    def test_clear_all(self):
        wm = WorkingMemory()
        wm.set("a", "1")
        wm.set("b", "2")
        wm.clear_all()
        assert wm.get("a") is None

    def test_snapshot(self):
        wm = WorkingMemory()
        wm.set("x", "10", task_id="t")
        snap = wm.snapshot("t")
        assert snap == {"x": "10"}


class TestEpisodicMemory:
    def test_record_and_count(self, tmp_path):
        ep = EpisodicMemory(path=str(tmp_path / "ep.json"))
        ep.record(Episode(task="test task", agent="bot", action="run", result="ok"))
        assert ep.count() == 1

    def test_recent(self, tmp_path):
        ep = EpisodicMemory(path=str(tmp_path / "ep.json"))
        for i in range(5):
            ep.record(Episode(task=f"task {i}", agent="bot", action="run", result="ok"))
        recent = ep.recent(2)
        assert len(recent) == 2
        assert recent[0].task == "task 3"

    def test_search(self, tmp_path):
        ep = EpisodicMemory(path=str(tmp_path / "ep.json"))
        ep.record(Episode(task="deploy production", agent="bot", action="deploy", result="ok"))
        ep.record(Episode(task="run tests", agent="bot", action="test", result="ok"))
        results = ep.search("deploy")
        assert len(results) == 1
        assert "deploy" in results[0].task

    def test_failures(self, tmp_path):
        ep = EpisodicMemory(path=str(tmp_path / "ep.json"))
        ep.record(Episode(task="ok", agent="b", action="a", result="r", success=True))
        ep.record(Episode(task="fail", agent="b", action="a", result="r", success=False))
        failures = ep.failures()
        assert len(failures) == 1
        assert not failures[0].success

    def test_lessons(self, tmp_path):
        ep = EpisodicMemory(path=str(tmp_path / "ep.json"))
        ep.record(Episode(task="t", agent="b", action="a", result="r", reflection="lesson learned"))
        assert ep.lessons() == ["lesson learned"]

    def test_save_and_load(self, tmp_path):
        path = str(tmp_path / "episodes.json")
        ep = EpisodicMemory(path=path)
        ep.record(Episode(task="test", agent="b", action="a", result="r"))
        ep.save()
        ep2 = EpisodicMemory(path=path)
        assert ep2.count() == 1


class TestSemanticMemory:
    def test_learn_and_query(self, tmp_path):
        sm = SemanticMemory(path=str(tmp_path / "sem.json"))
        sm.learn(Fact(subject="Python", predicate="is", obj="a programming language"))
        results = sm.query(subject="Python")
        assert len(results) == 1
        assert results[0].obj == "a programming language"

    def test_know(self, tmp_path):
        sm = SemanticMemory(path=str(tmp_path / "sem.json"))
        sm.learn(Fact(subject="Earth", predicate="orbits", obj="the Sun"))
        assert sm.know("Earth", "orbits", "the Sun")
        assert not sm.know("Earth", "orbits", "Mars")

    def test_confidence_increase(self, tmp_path):
        sm = SemanticMemory(path=str(tmp_path / "sem.json"))
        f = Fact(subject="X", predicate="is", obj="Y", confidence=0.5)
        sm.learn(f)
        sm.learn(f)
        assert sm._facts[f.key()].confidence > 0.5
        assert sm._facts[f.key()].count == 2

    def test_patterns(self, tmp_path):
        sm = SemanticMemory(path=str(tmp_path / "sem.json"))
        sm.add_pattern({"tag": "user_pref", "data": "dark mode"})
        sm.add_pattern({"tag": "language", "data": "python"})
        assert len(sm.patterns(tag="user_pref")) == 1
        assert len(sm.patterns()) == 2

    def test_save_and_load(self, tmp_path):
        path = str(tmp_path / "sem.json")
        sm = SemanticMemory(path=path)
        sm.learn(Fact(subject="A", predicate="is", obj="B"))
        sm.save()
        sm2 = SemanticMemory(path=path)
        assert sm2.count_facts() == 1

    def test_clear(self, tmp_path):
        sm = SemanticMemory(path=str(tmp_path / "sem.json"))
        sm.learn(Fact(subject="A", predicate="is", obj="B"))
        sm.clear()
        assert sm.count_facts() == 0


class TestConsolidationEngine:
    def test_extract_facts(self):
        ce = ConsolidationEngine()
        facts = ce._extract_facts("Python is a programming language designed for readability.")
        assert len(facts) >= 1
        assert any("Python" in f.subject for f in facts)

    def test_consolidate_conversation(self, tmp_path):
        sm = SemanticMemory(path=str(tmp_path / "sem.json"))
        ce = ConsolidationEngine(semantic=sm)
        msg = {"role": "user", "content": "Flask is a web framework for Python."}
        facts = ce.consolidate_conversation([msg])
        assert len(facts) >= 1
        assert sm.count_facts() >= 1

    def test_consolidate_episode(self, tmp_path):
        sm = SemanticMemory(path=str(tmp_path / "sem.json"))
        ce = ConsolidationEngine(semantic=sm)
        facts = ce.consolidate_episode("build api", "FastAPI provides automatic OpenAPI docs.")
        assert len(facts) >= 1
        assert sm.count_facts() >= 1

    def test_empty_message_skipped(self, tmp_path):
        sm = SemanticMemory(path=str(tmp_path / "sem.json"))
        ce = ConsolidationEngine(semantic=sm)
        facts = ce.consolidate_conversation(
            [
                {"role": "system", "content": ""},
                {"role": "user", "content": "short"},
            ]
        )
        assert len(facts) == 0


class TestMemoryEngine:
    @pytest.mark.asyncio
    async def test_record_conversation(self, tmp_path):
        me = MemoryEngine(
            store=MemoryStore(path=str(tmp_path / "mem.json")),
            episodic=EpisodicMemory(path=str(tmp_path / "ep.json")),
            semantic=SemanticMemory(path=str(tmp_path / "sem.json")),
        )
        await me.record_conversation("user", "hello")
        ctx = await me.recall_context()
        assert "hello" in ctx

    @pytest.mark.asyncio
    async def test_record_episode(self, tmp_path):
        me = MemoryEngine(
            episodic=EpisodicMemory(path=str(tmp_path / "ep.json")),
            semantic=SemanticMemory(path=str(tmp_path / "sem.json")),
        )
        await me.record_episode(
            task="test deploy",
            agent="bot",
            action="deploy",
            result="successful deployment",
        )
        similar = await me.recall_similar_episodes("deploy")
        assert len(similar) >= 1

    @pytest.mark.asyncio
    async def test_recall_facts(self, tmp_path):
        me = MemoryEngine(
            semantic=SemanticMemory(path=str(tmp_path / "sem.json")),
        )
        me.semantic.learn(Fact(subject="Lumina", predicate="is", obj="an AI OS"))
        facts = await me.recall_facts(subject="Lumina")
        assert len(facts) == 1

    @pytest.mark.asyncio
    async def test_working_memory(self, tmp_path):
        me = MemoryEngine()
        me.working.set("key", "val", task_id="task1")
        assert me.working.get("key", task_id="task1") == "val"

    def test_build_context_prompt(self, tmp_path):
        me = MemoryEngine(
            store=MemoryStore(path=str(tmp_path / "mem.json")),
            episodic=EpisodicMemory(path=str(tmp_path / "ep.json")),
            semantic=SemanticMemory(path=str(tmp_path / "sem.json")),
        )
        me.store.add_conversation("user", "hello world")
        me.semantic.learn(Fact(subject="Test", predicate="is", obj="a fact"))
        prompt = me.build_context_prompt("test")
        assert "## Recent Conversation" in prompt
        assert "hello world" in prompt

    def test_save_all(self, tmp_path):
        ep_path = str(tmp_path / "ep.json")
        sem_path = str(tmp_path / "sem.json")
        me = MemoryEngine(
            episodic=EpisodicMemory(path=ep_path),
            semantic=SemanticMemory(path=sem_path),
        )
        me.episodic.record(Episode(task="t", agent="a", action="b", result="c"))
        me.semantic.learn(Fact("X", "is", "Y"))
        me.save_all()
        ep2 = EpisodicMemory(path=ep_path)
        sem2 = SemanticMemory(path=sem_path)
        assert ep2.count() == 1
        assert sem2.count_facts() == 1
