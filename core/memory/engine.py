from __future__ import annotations

from typing import Any

from core.memory.consolidation import ConsolidationEngine
from core.memory.embeddings import DummyEmbeddingProvider, EmbeddingProvider
from core.memory.episodic import Episode, EpisodicMemory
from core.memory.long_term import LongTermMemory
from core.memory.recall import RecallEngine
from core.memory.semantic import Fact, SemanticMemory
from core.memory.short_term import ShortTermMemory
from core.memory.store import MemoryStore
from core.memory.vector_store import InMemoryVectorStore, VectorRecord
from core.memory.working import WorkingMemory


class MemoryEngine:
    """Central memory system coordinating all memory types."""

    def __init__(
        self,
        store: MemoryStore | None = None,
        working: WorkingMemory | None = None,
        episodic: EpisodicMemory | None = None,
        semantic: SemanticMemory | None = None,
        consolidation: ConsolidationEngine | None = None,
        short_term: ShortTermMemory | None = None,
        long_term: LongTermMemory | None = None,
        vector_store: InMemoryVectorStore | None = None,
        embeddings: EmbeddingProvider | None = None,
    ):
        self.store = store or MemoryStore()
        self.working = working or WorkingMemory()
        self.episodic = episodic or EpisodicMemory()
        self.semantic = semantic or SemanticMemory()
        self.consolidation = consolidation or ConsolidationEngine(self.semantic)
        self.short_term = short_term or ShortTermMemory()
        self.long_term = long_term or LongTermMemory()
        self.vector_store = vector_store or InMemoryVectorStore()
        self.embeddings = embeddings or DummyEmbeddingProvider()
        self.recall_engine = RecallEngine(
            short_term=self.short_term,
            long_term=self.long_term,
            episodic=self.episodic,
            semantic=self.semantic,
            store=self.store,
            vector_store=self.vector_store,
            embeddings=self.embeddings,
        )

    async def record_conversation(self, role: str, content: str) -> None:
        self.store.add_conversation(role, content)
        self.short_term.add(role, content)

    async def record_episode(
        self,
        task: str,
        agent: str = "",
        action: str = "",
        result: str = "",
        reflection: str = "",
        duration_ms: float = 0.0,
        success: bool = True,
    ) -> None:
        ep = Episode(
            task=task,
            agent=agent,
            action=action,
            result=result,
            reflection=reflection,
            duration_ms=duration_ms,
            success=success,
        )
        self.episodic.record(ep)
        if success and result:
            self.consolidation.consolidate_episode(task, result, agent)

    async def recall_context(self, limit: int = 10) -> str:
        return self.store.get_recent_context(limit)

    async def recall_similar_episodes(self, task: str, limit: int = 3) -> list[Episode]:
        return self.episodic.search(task, limit=limit)

    async def recall_facts(self, subject: str = "", min_confidence: float = 0.0) -> list[Fact]:
        return self.semantic.query(subject=subject, min_confidence=min_confidence)

    async def recall_lessons(self) -> list[str]:
        return self.episodic.lessons()

    def recall(self, query: str, limit: int = 10) -> list[dict]:
        return [
            {"content": r.content, "score": r.score, "source": r.source}
            for r in self.recall_engine.recall(query, limit=limit)
        ]

    def recall_recent(self, n: int = 10) -> list[dict]:
        return [
            {"role": e.role, "content": e.content[:200]}
            for e in self.recall_engine.recall_recent(n)
        ]

    def recall_context_prompt(self, task: str, max_turns: int = 10) -> str:
        ctx = self.recall_engine.recall_context(task, max_turns=max_turns)
        return ctx.to_prompt(max_turns=max_turns)

    def remember_long_term(
        self, key: str, value: str, namespace: str = "default",
        tags: list[str] | None = None,
    ) -> None:
        self.long_term.remember(key, value, namespace=namespace, tags=tags)

    def recall_long_term(self, key: str, namespace: str = "default") -> str | None:
        return self.long_term.recall(key, namespace=namespace)

    def vector_add(
        self, id: str, vector: list[float], content: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.vector_store.add(
            VectorRecord(id=id, vector=vector, content=content, metadata=metadata or {}),
        )

    def vector_search(self, query_vector: list[float], top_k: int = 10) -> list[tuple[str, float]]:
        return [(r.id, s) for r, s in self.vector_store.search(query_vector, top_k=top_k)]

    def build_context_prompt(self, task: str, limit: int = 5) -> str:
        ctx = self.recall_engine.recall_context(task, max_turns=limit)
        prompt = ctx.to_prompt(max_turns=limit)
        if "## Recent Conversation" not in prompt:
            store_context = self.store.get_recent_context(limit)
            if store_context.strip():
                prompt = f"## Recent Conversation\n{store_context}\n\n{prompt}"
        return prompt

    def save_all(self) -> None:
        self.episodic.save()
        self.semantic.save()
