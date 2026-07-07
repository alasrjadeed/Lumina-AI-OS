from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.memory.embeddings import DummyEmbeddingProvider, EmbeddingProvider
from core.memory.episodic import EpisodicMemory
from core.memory.long_term import LongTermMemory
from core.memory.semantic import SemanticMemory
from core.memory.short_term import ShortTermMemory
from core.memory.vector_store import InMemoryVectorStore, cosine_similarity


@dataclass
class SearchResult:
    content: str
    score: float
    source: str
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class MemorySearch:
    """Unified search across all memory layers with hybrid scoring."""

    def __init__(
        self,
        short_term: ShortTermMemory | None = None,
        long_term: LongTermMemory | None = None,
        episodic: EpisodicMemory | None = None,
        semantic: SemanticMemory | None = None,
        vector_store: InMemoryVectorStore | None = None,
        embeddings: EmbeddingProvider | None = None,
    ):
        self.short_term = short_term
        self.long_term = long_term
        self.episodic = episodic
        self.semantic = semantic
        self.vector_store = vector_store
        self.embeddings = embeddings or DummyEmbeddingProvider()

    def search(
        self,
        query: str,
        limit: int = 10,
        sources: list[str] | None = None,
    ) -> list[SearchResult]:
        results: list[SearchResult] = []
        query_vec = self.embeddings.embed(query)

        if (sources is None or "short_term" in sources) and self.short_term:
            for e in self.short_term.search(query, limit=limit * 2):
                score = self._score(e.content, query, query_vec)
                results.append(SearchResult(
                    content=e.content,
                    score=score,
                    source="short_term",
                    timestamp=e.timestamp,
                    metadata={"role": e.role},
                ))

        if (sources is None or "long_term" in sources) and self.long_term:
            for e in self.long_term.search_content(query):
                score = self._score(e.value, query, query_vec)
                results.append(SearchResult(
                    content=e.value,
                    score=score,
                    source="long_term",
                    timestamp=e.timestamp,
                    metadata={"key": e.key, "tags": e.tags},
                ))

        if (sources is None or "episodic" in sources) and self.episodic:
            for ep in self.episodic.search(query, limit=limit * 2):
                combined = f"{ep.task} {ep.result} {ep.reflection}"
                score = self._score(combined, query, query_vec)
                results.append(SearchResult(
                    content=combined,
                    score=score,
                    source="episodic",
                    timestamp=0.0,
                    metadata={"task": ep.task, "success": ep.success},
                ))

        if (sources is None or "semantic" in sources) and self.semantic:
            for fact in self.semantic.query():
                combined = f"{fact.subject} {fact.predicate} {fact.obj}"
                score = self._score(combined, query, query_vec)
                results.append(SearchResult(
                    content=combined,
                    score=score * fact.confidence,
                    source="semantic",
                    metadata={"subject": fact.subject, "confidence": fact.confidence},
                ))

        if (sources is None or "vector" in sources) and self.vector_store:
            for rec, sim in self.vector_store.search(query_vec, top_k=limit * 2):
                results.append(SearchResult(
                    content=rec.content or "",
                    score=sim,
                    source="vector",
                    metadata=rec.metadata,
                ))

        results.sort(key=lambda r: -r.score)
        seen = set()
        deduped = []
        for r in results:
            dedup_key = r.content[:100]
            if dedup_key not in seen:
                seen.add(dedup_key)
                deduped.append(r)
        return deduped[:limit]

    def _score(self, text: str, query: str, query_vec: list[float]) -> float:
        content_lower = text.lower()
        tokens = [t for t in query.lower().split() if len(t) > 2]
        if tokens:
            matches = sum(1 for t in tokens if t in content_lower)
            keyword_score = matches / len(tokens)
        else:
            keyword_score = 1.0 if query.lower() in content_lower else 0.0
        if query_vec:
            text_vec = self.embeddings.embed(text[:1000])
            semantic_score = cosine_similarity(query_vec, text_vec)
        else:
            semantic_score = 0.0
        return 0.3 * keyword_score + 0.7 * semantic_score
