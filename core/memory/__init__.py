"""Memory system — multi-layer persistent and ephemeral storage.

Working memory (task-scoped TTL), episodic memory (past runs),
semantic memory (facts/patterns), short-term (conversation buffer),
long-term (persistent KV), vector store (cosine similarity search),
embeddings, unified search, and recall engine.
"""

from core.memory.consolidation import ConsolidationEngine
from core.memory.embeddings import DummyEmbeddingProvider, OpenAIEmbeddingProvider
from core.memory.engine import MemoryEngine
from core.memory.episodic import EpisodicMemory
from core.memory.long_term import JsonFileBackend, LongTermMemory, SqliteBackend
from core.memory.recall import RecallContext, RecallEngine
from core.memory.search import MemorySearch, SearchResult
from core.memory.semantic import SemanticMemory
from core.memory.short_term import ShortTermEntry, ShortTermMemory
from core.memory.store import MemoryStore, memory
from core.memory.vector_store import InMemoryVectorStore, VectorRecord
from core.memory.working import WorkingMemory

__all__ = [
    "MemoryEngine",
    "MemoryStore",
    "memory",
    "WorkingMemory",
    "ShortTermMemory",
    "ShortTermEntry",
    "LongTermMemory",
    "JsonFileBackend",
    "SqliteBackend",
    "InMemoryVectorStore",
    "VectorRecord",
    "DummyEmbeddingProvider",
    "OpenAIEmbeddingProvider",
    "MemorySearch",
    "SearchResult",
    "RecallEngine",
    "RecallContext",
    "EpisodicMemory",
    "SemanticMemory",
    "ConsolidationEngine",
]
