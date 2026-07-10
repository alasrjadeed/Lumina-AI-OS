from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class VectorRecord:
    id: str
    vector: list[float]
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class VectorStore(Protocol):
    def add(self, record: VectorRecord) -> None: ...
    def add_many(self, records: list[VectorRecord]) -> None: ...
    def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
    ) -> list[tuple[VectorRecord, float]]: ...
    def get(self, id: str) -> VectorRecord | None: ...
    def delete(self, id: str) -> bool: ...
    def count(self) -> int: ...
    def clear(self) -> None: ...


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class InMemoryVectorStore:
    """Brute-force in-memory vector store with cosine similarity."""

    def __init__(self):
        self._records: dict[str, VectorRecord] = {}

    def add(self, record: VectorRecord) -> None:
        self._records[record.id] = record

    def add_many(self, records: list[VectorRecord]) -> None:
        for r in records:
            self.add(r)

    def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
    ) -> list[tuple[VectorRecord, float]]:
        scored = []
        for record in self._records.values():
            sim = cosine_similarity(query_vector, record.vector)
            scored.append((record, sim))
        scored.sort(key=lambda x: -x[1])
        return scored[:top_k]

    def get(self, id: str) -> VectorRecord | None:
        return self._records.get(id)

    def delete(self, id: str) -> bool:
        if id in self._records:
            del self._records[id]
            return True
        return False

    def count(self) -> int:
        return len(self._records)

    def clear(self) -> None:
        self._records.clear()
