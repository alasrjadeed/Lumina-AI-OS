from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.memory.embeddings import DummyEmbeddingProvider, EmbeddingProvider
from core.memory.episodic import EpisodicMemory
from core.memory.long_term import LongTermMemory
from core.memory.search import MemorySearch, SearchResult
from core.memory.semantic import SemanticMemory
from core.memory.short_term import ShortTermEntry, ShortTermMemory
from core.memory.store import MemoryStore
from core.memory.vector_store import InMemoryVectorStore


@dataclass
class RecallContext:
    recent_conversation: list[ShortTermEntry] = field(default_factory=list)
    similar_episodes: list[SearchResult] = field(default_factory=list)
    relevant_facts: list[SearchResult] = field(default_factory=list)
    long_term_memories: list[SearchResult] = field(default_factory=list)
    search_results: list[SearchResult] = field(default_factory=list)

    def to_prompt(self, max_turns: int = 10) -> str:
        parts: list[str] = []

        recent = self.recent_conversation[-max_turns:]
        if recent:
            parts.append(
                "## Recent Conversation\n"
                + "\n".join(f"{e.role}: {e.content[:300]}" for e in recent)
            )

        if self.similar_episodes:
            similar_lines = "\n".join(
                f"- {r.content[:200]} (score: {r.score:.2f})"
                for r in self.similar_episodes[:3]
            )
            parts.append("## Similar Past Episodes\n" + similar_lines)

        if self.relevant_facts:
            parts.append(
                "## Known Facts\n"
                + "\n".join(f"- {r.content[:200]}" for r in self.relevant_facts[:5])
            )

        if self.long_term_memories:
            parts.append(
                "## Long-Term Memories\n"
                + "\n".join(f"- {r.content[:200]}" for r in self.long_term_memories[:5])
            )

        return "\n\n".join(parts)


class RecallEngine:
    """Unified recall interface querying all memory layers."""

    def __init__(
        self,
        short_term: ShortTermMemory | None = None,
        long_term: LongTermMemory | None = None,
        episodic: EpisodicMemory | None = None,
        semantic: SemanticMemory | None = None,
        store: MemoryStore | None = None,
        vector_store: InMemoryVectorStore | None = None,
        embeddings: EmbeddingProvider | None = None,
    ):
        self.short_term = short_term or ShortTermMemory()
        self.long_term = long_term or LongTermMemory()
        self.episodic = episodic or EpisodicMemory()
        self.semantic = semantic or SemanticMemory()
        self.store = store or MemoryStore()
        self.vector_store = vector_store or InMemoryVectorStore()
        self.embeddings = embeddings or DummyEmbeddingProvider()
        self.search_engine = MemorySearch(
            short_term=self.short_term,
            long_term=self.long_term,
            episodic=self.episodic,
            semantic=self.semantic,
            vector_store=self.vector_store,
            embeddings=self.embeddings,
        )

    def recall(
        self, query: str, limit: int = 10,
        sources: list[str] | None = None,
    ) -> list[SearchResult]:
        return self.search_engine.search(query, limit=limit, sources=sources)

    def recall_recent(self, n: int = 10) -> list[ShortTermEntry]:
        return self.short_term.get_recent(n)

    def recall_relevant(self, query: str, n: int = 5) -> list[SearchResult]:
        return self.search_engine.search(query, limit=n)

    def recall_context(self, task: str, max_turns: int = 10) -> RecallContext:
        ctx = RecallContext()
        ctx.recent_conversation = self.short_term.get_recent(max_turns)
        ctx.similar_episodes = self.search_engine.search(task, limit=5, sources=["episodic"])
        ctx.relevant_facts = self.search_engine.search(task, limit=5, sources=["semantic"])
        ctx.long_term_memories = self.search_engine.search(task, limit=5, sources=["long_term"])
        ctx.search_results = self.search_engine.search(task, limit=10)
        return ctx

    def record_conversation(
        self, role: str, content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.short_term.add(role, content, metadata)
        self.store.add_conversation(role, content)
