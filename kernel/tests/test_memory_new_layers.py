from __future__ import annotations

import asyncio
import time
from pathlib import Path

import pytest

from core.memory.embeddings import DummyEmbeddingProvider
from core.memory.engine import MemoryEngine
from core.memory.long_term import JsonFileBackend, LongTermMemory, SqliteBackend
from core.memory.recall import RecallEngine
from core.memory.search import MemorySearch
from core.memory.short_term import ShortTermEntry, ShortTermMemory
from core.memory.vector_store import InMemoryVectorStore, VectorRecord, cosine_similarity


class TestShortTermMemory:
    def test_add_and_get_recent(self):
        stm = ShortTermMemory(max_size=10)
        stm.add("user", "hello")
        stm.add("assistant", "hi there")
        recent = stm.get_recent(2)
        assert len(recent) == 2
        assert recent[0].role == "user"
        assert recent[1].role == "assistant"

    def test_max_size_eviction(self):
        stm = ShortTermMemory(max_size=5)
        for i in range(10):
            stm.add("user", f"msg-{i}")
        assert len(stm.get_all()) <= 5

    def test_priority_retention(self):
        stm = ShortTermMemory(max_size=4)
        stm.add("system", "keep-me")
        for i in range(5):
            stm.add("user", f"msg-{i}")
        all_entries = stm.get_all()
        roles = [e.role for e in all_entries]
        assert "system" in roles

    def test_search(self):
        stm = ShortTermMemory(max_size=20)
        stm.add("user", "what is the weather in paris")
        stm.add("assistant", "it is sunny in paris")
        stm.add("user", "hello world")
        results = stm.search("paris")
        assert len(results) >= 1
        assert "paris" in results[0].content.lower()

    def test_clear(self):
        stm = ShortTermMemory(max_size=10)
        stm.add("user", "hello")
        stm.clear()
        assert len(stm.get_all()) == 0

    def test_entry_dataclass(self):
        e = ShortTermEntry(role="user", content="test", metadata={"key": "val"})
        assert e.role == "user"
        assert e.metadata["key"] == "val"
        assert e.priority == 1

    def test_evict_keeps_highest_priority(self):
        stm = ShortTermMemory(max_size=3)
        stm.add("system", "sys-msg")
        stm.add("user", "user-msg-1")
        stm.add("user", "user-msg-2")
        stm.add("user", "user-msg-3")
        remaining = stm.get_all()
        assert any(e.role == "system" for e in remaining)


class TestLongTermMemory:
    def test_json_backend_remember_and_recall(self, tmp_path: Path):
        path = str(tmp_path / "test_memory.json")
        backend = JsonFileBackend(path)
        ltm = LongTermMemory(backend)
        ltm.remember("name", "Alice", namespace="user")
        assert ltm.recall("name", namespace="user") == "Alice"

    def test_recall_missing(self):
        ltm = LongTermMemory()
        assert ltm.recall("nonexistent") is None

    def test_forget(self, tmp_path: Path):
        path = str(tmp_path / "test_forget.json")
        backend = JsonFileBackend(path)
        ltm = LongTermMemory(backend)
        ltm.remember("key1", "val1")
        assert ltm.forget("key1") is True
        assert ltm.forget("key1") is False

    def test_ttl_expiry(self, tmp_path: Path):
        path = str(tmp_path / "test_ttl.json")
        backend = JsonFileBackend(path)
        ltm = LongTermMemory(backend)
        ltm.remember("temp", "expire soon", ttl=0.01)
        time.sleep(0.02)
        assert ltm.recall("temp") is None

    def test_list_namespace(self, tmp_path: Path):
        path = str(tmp_path / "test_list.json")
        backend = JsonFileBackend(path)
        ltm = LongTermMemory(backend)
        ltm.remember("a", "1", namespace="ns1")
        ltm.remember("b", "2", namespace="ns1")
        ltm.remember("c", "3", namespace="ns2")
        assert len(ltm.list("ns1")) == 2
        assert len(ltm.list("ns2")) == 1

    def test_search_by_tags(self, tmp_path: Path):
        path = str(tmp_path / "test_tags.json")
        backend = JsonFileBackend(path)
        ltm = LongTermMemory(backend)
        ltm.remember("k1", "val1", tags=["alpha", "beta"])
        ltm.remember("k2", "val2", tags=["beta", "gamma"])
        ltm.remember("k3", "val3", tags=["gamma"])
        results = ltm.search_by_tags(["alpha"])
        assert len(results) == 1
        assert results[0].key == "k1"

    def test_search_content(self, tmp_path: Path):
        path = str(tmp_path / "test_content.json")
        backend = JsonFileBackend(path)
        ltm = LongTermMemory(backend)
        ltm.remember("k1", "the quick brown fox")
        ltm.remember("k2", "jumps over the lazy dog")
        results = ltm.search_content("fox")
        assert len(results) == 1

    def test_clear_namespace(self, tmp_path: Path):
        path = str(tmp_path / "test_clear.json")
        backend = JsonFileBackend(path)
        ltm = LongTermMemory(backend)
        ltm.remember("k1", "v1")
        ltm.remember("k2", "v2")
        ltm.clear()
        assert len(ltm.list()) == 0

    def test_sqlite_backend(self, tmp_path: Path):
        path = str(tmp_path / "test_sqlite.db")
        backend = SqliteBackend(path)
        ltm = LongTermMemory(backend)
        ltm.remember("name", "Bob", namespace="test")
        assert ltm.recall("name", namespace="test") == "Bob"
        ltm.close()

    @pytest.mark.parametrize("backend_cls", [JsonFileBackend, SqliteBackend])
    def test_both_backends(self, backend_cls, tmp_path: Path):
        if backend_cls is JsonFileBackend:
            path = str(tmp_path / "test.json")
        else:
            path = str(tmp_path / "test.db")
        backend = backend_cls(path)
        ltm = LongTermMemory(backend)
        ltm.remember("k", "v", namespace="test", tags=["tag1"])
        assert ltm.recall("k", namespace="test") == "v"
        results = ltm.search_by_tags(["tag1"], namespace="test")
        assert len(results) == 1
        ltm.close()


class TestVectorStore:
    def test_add_and_search(self):
        vs = InMemoryVectorStore()
        vs.add(VectorRecord(id="1", vector=[1.0, 0.0, 0.0], content="hello"))
        vs.add(VectorRecord(id="2", vector=[0.0, 1.0, 0.0], content="world"))
        vs.add(VectorRecord(id="3", vector=[0.9, 0.1, 0.0], content="hello again"))
        results = vs.search([1.0, 0.0, 0.0], top_k=2)
        assert len(results) == 2
        assert results[0][0].id == "1"
        assert results[0][1] > 0.9

    def test_get(self):
        vs = InMemoryVectorStore()
        r = VectorRecord(id="test", vector=[1.0, 2.0])
        vs.add(r)
        assert vs.get("test") is r
        assert vs.get("nonexistent") is None

    def test_delete(self):
        vs = InMemoryVectorStore()
        vs.add(VectorRecord(id="del", vector=[1.0]))
        assert vs.delete("del") is True
        assert vs.delete("del") is False

    def test_count_and_clear(self):
        vs = InMemoryVectorStore()
        vs.add_many([VectorRecord(id=str(i), vector=[float(i)]) for i in range(5)])
        assert vs.count() == 5
        vs.clear()
        assert vs.count() == 0

    def test_cosine_similarity(self):
        assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
        assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
        assert cosine_similarity([], []) == 0.0
        assert cosine_similarity([3.0, 4.0], [3.0, 4.0]) == 1.0

    def test_search_empty(self):
        vs = InMemoryVectorStore()
        assert vs.search([1.0, 0.0]) == []


class TestEmbeddings:
    def test_dummy_embedding_dimensions(self):
        de = DummyEmbeddingProvider(dimensions=64)
        vec = de.embed("hello world")
        assert len(vec) == 64

    def test_dummy_embedding_deterministic(self):
        de = DummyEmbeddingProvider()
        v1 = de.embed("same text")
        v2 = de.embed("same text")
        assert v1 == v2

    def test_dummy_embedding_different_inputs(self):
        de = DummyEmbeddingProvider(dimensions=16)
        v1 = de.embed("cat")
        v2 = de.embed("dog")
        assert v1 != v2

    def test_embed_many(self):
        de = DummyEmbeddingProvider(dimensions=8)
        results = de.embed_many(["one", "two", "three"])
        assert len(results) == 3
        assert all(len(v) == 8 for v in results)

    def test_similarity_of_identical_texts(self):
        de = DummyEmbeddingProvider(dimensions=16)
        v1 = de.embed("hello")
        v2 = de.embed("hello")
        assert cosine_similarity(v1, v2) > 0.99


class TestMemorySearch:
    def test_search_with_short_term(self):
        stm = ShortTermMemory(max_size=20)
        stm.add("user", "what is the capital of france")
        stm.add("assistant", "paris is the capital of france")
        ms = MemorySearch(short_term=stm)
        results = ms.search("france capital")
        assert len(results) >= 1

    def test_search_with_long_term(self, tmp_path: Path):
        path = str(tmp_path / "search_lt.json")
        ltm = LongTermMemory(JsonFileBackend(path))
        ltm.remember("fact", "paris is the capital of france", tags=["geography"])
        ms = MemorySearch(long_term=ltm)
        results = ms.search("paris capital")
        assert len(results) >= 1
        assert "france" in results[0].content.lower()

    def test_search_respects_limit(self):
        stm = ShortTermMemory(max_size=50)
        for i in range(20):
            stm.add("user", f"query about paris {i}")
        ms = MemorySearch(short_term=stm)
        results = ms.search("paris", limit=5)
        assert len(results) <= 5

    def test_search_sources_filter(self):
        stm = ShortTermMemory(max_size=10)
        stm.add("user", "weather in london")
        ms = MemorySearch(short_term=stm)
        results = ms.search("london", sources=["long_term"])
        assert len(results) == 0

    def test_search_with_vector_store(self):
        vs = InMemoryVectorStore()
        de = DummyEmbeddingProvider(dimensions=8)
        vec = de.embed("paris france capital")
        vs.add(VectorRecord(id="p1", vector=vec, content="paris is the capital of france"))
        ms = MemorySearch(vector_store=vs, embeddings=de)
        results = ms.search("france capital")
        assert len(results) >= 1


class TestRecallEngine:
    def test_recall_basic(self):
        stm = ShortTermMemory(max_size=20)
        stm.add("user", "hello")
        stm.add("assistant", "hi")
        re = RecallEngine(short_term=stm)
        results = re.recall("hello")
        assert len(results) >= 1

    def test_recall_recent(self):
        stm = ShortTermMemory(max_size=20)
        stm.add("user", "first")
        stm.add("assistant", "second")
        stm.add("user", "third")
        re = RecallEngine(short_term=stm)
        recent = re.recall_recent(2)
        assert len(recent) == 2
        assert recent[0].content == "second"
        assert recent[1].content == "third"

    def test_recall_context_structure(self):
        stm = ShortTermMemory(max_size=20)
        stm.add("user", "what is the weather")
        stm.add("assistant", "it is sunny")
        re = RecallEngine(short_term=stm)
        ctx = re.recall_context("weather")
        assert len(ctx.recent_conversation) >= 1
        prompt = ctx.to_prompt()
        assert "Recent Conversation" in prompt

    def test_record_conversation(self):
        stm = ShortTermMemory(max_size=10)
        re = RecallEngine(short_term=stm)
        re.record_conversation("user", "hello there")
        recent = re.recall_recent(1)
        assert len(recent) == 1
        assert recent[0].content == "hello there"

    def test_recall_context_to_prompt_with_all_sources(self, tmp_path: Path):
        stm = ShortTermMemory(max_size=20)
        stm.add("user", "hello from the test")
        stm.add("assistant", "hi, i am an assistant")
        ltm = LongTermMemory(JsonFileBackend(str(tmp_path / "ctx_test.json")))
        ltm.remember("greeting", "the assistant always greets politely")
        re = RecallEngine(short_term=stm, long_term=ltm)
        ctx = re.recall_context("hello")
        prompt = ctx.to_prompt()
        assert "Recent Conversation" in prompt


class TestMemoryEngineIntegration:
    def test_memory_engine_creates_new_layers(self):
        me = MemoryEngine()
        assert me.short_term is not None
        assert me.long_term is not None
        assert me.vector_store is not None
        assert me.embeddings is not None
        assert me.recall_engine is not None

    def test_record_conversation_with_short_term(self):
        me = MemoryEngine()
        asyncio.run(me.record_conversation("user", "test message"))
        recent = me.recall_recent(1)
        assert len(recent) == 1
        assert recent[0]["role"] == "user"

    def test_long_term_via_memory_engine(self):
        me = MemoryEngine()
        me.remember_long_term("mood", "happy", tags=["emotion"])
        assert me.recall_long_term("mood") == "happy"

    def test_vector_via_memory_engine(self):
        me = MemoryEngine()
        vec = me.embeddings.embed("test vector")
        me.vector_add("v1", vec, content="test content")
        results = me.vector_search(vec, top_k=1)
        assert len(results) == 1
        assert results[0][0] == "v1"

    def test_recall_context_prompt(self):
        me = MemoryEngine()
        asyncio.run(me.record_conversation("user", "what is the capital of france"))
        asyncio.run(me.record_conversation("assistant", "paris"))
        prompt = me.recall_context_prompt("france capital")
        assert "france" in prompt or "paris" in prompt

    def test_save_all(self):
        me = MemoryEngine()
        me.save_all()

    def test_recall_method(self):
        me = MemoryEngine()
        asyncio.run(me.record_conversation("user", "testing recall method"))
        results = me.recall("recall", limit=5)
        assert isinstance(results, list)
