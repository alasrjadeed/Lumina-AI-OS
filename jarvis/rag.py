from __future__ import annotations

import hashlib
import json
import os
import time

RAG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "jarvis_knowledge"
)
INDEX_PATH = os.path.join(RAG_DIR, "index.json")


class LocalRAG:
    def __init__(self, ollama_base_url: str = "http://localhost:11434"):
        self.ollama_base_url = ollama_base_url
        self.embed_model = "nomic-embed-text"
        self._documents: list[dict] = []
        self._embeddings: list[list[float]] = []
        os.makedirs(RAG_DIR, exist_ok=True)
        self._load_index()

    def _load_index(self) -> None:
        if os.path.exists(INDEX_PATH):
            try:
                with open(INDEX_PATH) as f:
                    data = json.load(f)
                self._documents = data.get("documents", [])
                self._embeddings = data.get("embeddings", [])
            except (json.JSONDecodeError, OSError):
                pass

    def _save_index(self) -> None:
        try:
            with open(INDEX_PATH, "w") as f:
                json.dump({"documents": self._documents, "embeddings": self._embeddings}, f)
        except OSError:
            pass

    def _chunk_text(self, text: str, chunk_size: int = 512) -> list[str]:
        words = text.split()
        chunks = [" ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)]
        return chunks

    def _get_embedding(self, text: str) -> list[float]:
        try:
            import httpx

            resp = httpx.post(
                f"{self.ollama_base_url}/api/embeddings",
                json={"model": self.embed_model, "prompt": text},
                timeout=30,
            )
            data = resp.json()
            return data.get("embedding", [])
        except Exception:
            return []

    def _cosine_sim(self, a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(x * x for x in b) ** 0.5
        if not na or not nb:
            return 0.0
        return dot / (na * nb)

    def index_file(self, file_path: str) -> int:
        try:
            with open(file_path) as f:
                text = f.read()
        except (OSError, UnicodeDecodeError):
            return 0

        doc_id = hashlib.md5(file_path.encode()).hexdigest()[:12]
        chunks = self._chunk_text(text)

        count = 0
        for i, chunk in enumerate(chunks):
            existing = [d for d in self._documents if d.get("id") == f"{doc_id}_{i}"]
            if existing:
                continue
            emb = self._get_embedding(chunk)
            if not emb:
                continue
            self._documents.append(
                {
                    "id": f"{doc_id}_{i}",
                    "file": file_path,
                    "text": chunk[:500],
                    "timestamp": time.time(),
                }
            )
            self._embeddings.append(emb)
            count += 1

        if count:
            self._save_index()
        return count

    def index_directory(self, directory: str, pattern: str = "*.py") -> int:
        import glob

        total = 0
        for f in glob.glob(os.path.join(directory, pattern)):
            total += self.index_file(f)
        for f in glob.glob(os.path.join(directory, "**", pattern), recursive=True):
            total += self.index_file(f)
        return total

    def query(self, question: str, top_k: int = 3) -> list[dict]:
        q_emb = self._get_embedding(question)
        if not q_emb or not self._embeddings:
            return []

        scored = []
        for i, doc_emb in enumerate(self._embeddings):
            sim = self._cosine_sim(q_emb, doc_emb)
            scored.append((sim, i))

        scored.sort(key=lambda x: -x[0])
        results = []
        for sim, i in scored[:top_k]:
            if sim < 0.3:
                continue
            results.append(
                {
                    "text": self._documents[i]["text"],
                    "file": self._documents[i]["file"],
                    "score": round(sim, 3),
                }
            )
        return results

    def context_for(self, question: str, max_chars: int = 1500) -> str:
        docs = self.query(question)
        if not docs:
            return ""
        parts = [f"[{d['file']}] (score: {d['score']}): {d['text']}" for d in docs]
        context = "\n\n".join(parts)
        return context[:max_chars]
