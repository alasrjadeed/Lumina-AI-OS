from __future__ import annotations

import hashlib
import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any

_RAG_DIR = os.path.expanduser("~/.lumina/rag")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


class RAGPipeline:
    def __init__(self):
        self._documents: list[dict] = []
        self._chunks: list[dict] = []
        self._load()

    def _path(self, name: str) -> str:
        os.makedirs(_RAG_DIR, exist_ok=True)
        return os.path.join(_RAG_DIR, name)

    def _load(self) -> None:
        doc_path = self._path("documents.json")
        if os.path.exists(doc_path):
            try:
                with open(doc_path) as f:
                    self._documents = json.load(f)
            except Exception:
                self._documents = []
        chunk_path = self._path("chunks.json")
        if os.path.exists(chunk_path):
            try:
                with open(chunk_path) as f:
                    self._chunks = json.load(f)
            except Exception:
                self._chunks = []

    def _save(self) -> None:
        with open(self._path("documents.json"), "w") as f:
            json.dump(self._documents, f, indent=2)
        with open(self._path("chunks.json"), "w") as f:
            json.dump(self._chunks, f, indent=2)

    def _chunk_text(self, text: str, source_id: str) -> list[dict]:
        words = re.split(r'\s+', text)
        chunks = []
        for i in range(0, len(words), CHUNK_SIZE - CHUNK_OVERLAP):
            chunk_words = words[i:i + CHUNK_SIZE]
            chunk_text = " ".join(chunk_words)
            if not chunk_text.strip():
                continue
            chunk_id = uuid.uuid4().hex[:8]
            chunks.append({
                "id": chunk_id,
                "source_id": source_id,
                "text": chunk_text,
                "index": len(chunks),
                "word_count": len(chunk_words),
            })
        return chunks

    def ingest_text(self, title: str, content: str, source: str = "manual", metadata: dict | None = None) -> dict:
        doc_id = uuid.uuid4().hex[:12]
        checksum = hashlib.md5(content.encode()).hexdigest()

        doc = {
            "id": doc_id,
            "title": title,
            "source": source,
            "metadata": metadata or {},
            "checksum": checksum,
            "char_count": len(content),
            "word_count": len(content.split()),
            "ingested_at": time.time(),
        }
        self._documents.append(doc)

        chunks = self._chunk_text(content, doc_id)
        self._chunks.extend(chunks)
        self._save()
        return {**doc, "chunk_count": len(chunks)}

    def ingest_file(self, file_path: str, title: str = "") -> dict | None:
        path = Path(file_path)
        if not path.exists():
            return None
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            try:
                content = path.read_bytes().decode("utf-8", errors="replace")
            except Exception:
                return None
        return self.ingest_text(title or path.stem, content, source=f"file:{path.name}")

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored = []
        for chunk in self._chunks:
            text_lower = chunk["text"].lower()
            word_match = sum(1 for w in query_words if w in text_lower)
            exact_match = query_lower in text_lower
            score = (3 if exact_match else 0) + word_match
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda x: -x[0])
        results = []
        for score, chunk in scored[:top_k]:
            doc = self._get_doc(chunk["source_id"])
            results.append({
                "chunk_id": chunk["id"],
                "text": chunk["text"][:500],
                "score": score,
                "source_id": chunk["source_id"],
                "doc_title": doc["title"] if doc else "Unknown",
                "doc_source": doc["source"] if doc else "",
            })
        return results

    def _get_doc(self, doc_id: str) -> dict | None:
        for d in self._documents:
            if d["id"] == doc_id:
                return d
        return None

    def list_documents(self) -> list[dict]:
        docs = []
        for d in self._documents:
            chunk_count = len([c for c in self._chunks if c["source_id"] == d["id"]])
            docs.append({**d, "chunk_count": chunk_count})
        return sorted(docs, key=lambda x: x["ingested_at"], reverse=True)

    def get_document(self, doc_id: str) -> dict | None:
        doc = self._get_doc(doc_id)
        if not doc:
            return None
        doc_chunks = [c for c in self._chunks if c["source_id"] == doc_id]
        return {**doc, "chunks": doc_chunks}

    def delete_document(self, doc_id: str) -> bool:
        for i, d in enumerate(self._documents):
            if d["id"] == doc_id:
                self._documents.pop(i)
                self._chunks = [c for c in self._chunks if c["source_id"] != doc_id]
                self._save()
                return True
        return False

    def get_stats(self) -> dict:
        return {
            "total_documents": len(self._documents),
            "total_chunks": len(self._chunks),
            "total_words": sum(d.get("word_count", 0) for d in self._documents),
        }


rag = RAGPipeline()
