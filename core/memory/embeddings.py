from __future__ import annotations

import hashlib
from typing import Protocol

import openai


class EmbeddingProvider(Protocol):
    def embed(self, text: str) -> list[float]: ...
    def embed_many(self, texts: list[str]) -> list[list[float]]: ...


class DummyEmbeddingProvider:
    """Hash-based deterministic embeddings for testing."""

    def __init__(self, dimensions: int = 64):
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        h = hashlib.sha256(text.encode()).digest()
        return [((h[i % 32] + (i // 32)) % 256) / 255.0 for i in range(self.dimensions)]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


class OpenAIEmbeddingProvider:
    """OpenAI embedding API wrapper."""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small", dimensions: int = 256):
        self.api_key = api_key
        self.model = model
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        client = openai.OpenAI(api_key=self.api_key)
        resp = client.embeddings.create(input=text, model=self.model, dimensions=self.dimensions)
        return resp.data[0].embedding

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        client = openai.OpenAI(api_key=self.api_key)
        resp = client.embeddings.create(input=texts, model=self.model, dimensions=self.dimensions)
        return [d.embedding for d in resp.data]
