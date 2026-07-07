from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class LongTermEntry:
    key: str
    value: str
    namespace: str = "default"
    tags: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    ttl: float | None = None

    @property
    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl


class LongTermBackend(Protocol):
    def get(self, namespace: str, key: str) -> LongTermEntry | None: ...
    def put(self, entry: LongTermEntry) -> None: ...
    def delete(self, namespace: str, key: str) -> bool: ...
    def list_namespace(self, namespace: str) -> list[LongTermEntry]: ...
    def search_tags(self, namespace: str, tags: list[str]) -> list[LongTermEntry]: ...
    def search_content(self, namespace: str, query: str) -> list[LongTermEntry]: ...
    def clear_namespace(self, namespace: str) -> None: ...
    def close(self) -> None: ...


class JsonFileBackend:
    def __init__(self, path: str = "lumina_long_term.json"):
        self.path = path
        self._data: dict[str, dict[str, dict]] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.path):
            with open(self.path) as f:
                self._data = json.load(f)

    def _save(self) -> None:
        with open(self.path, "w") as f:
            json.dump(self._data, f, indent=2)

    def get(self, namespace: str, key: str) -> LongTermEntry | None:
        raw = self._data.get(namespace, {}).get(key)
        if raw is None:
            return None
        entry = LongTermEntry(**raw)
        if entry.is_expired:
            self.delete(namespace, key)
            return None
        return entry

    def put(self, entry: LongTermEntry) -> None:
        ns = self._data.setdefault(entry.namespace, {})
        ns[entry.key] = {
            "key": entry.key,
            "value": entry.value,
            "namespace": entry.namespace,
            "tags": entry.tags,
            "timestamp": entry.timestamp,
            "ttl": entry.ttl,
        }
        self._save()

    def delete(self, namespace: str, key: str) -> bool:
        ns = self._data.get(namespace)
        if ns and key in ns:
            del ns[key]
            self._save()
            return True
        return False

    def list_namespace(self, namespace: str) -> list[LongTermEntry]:
        ns = self._data.get(namespace, {})
        result = []
        for raw in ns.values():
            entry = LongTermEntry(**raw)
            if not entry.is_expired:
                result.append(entry)
        return result

    def search_tags(self, namespace: str, tags: list[str]) -> list[LongTermEntry]:
        tag_set = set(tags)
        return [e for e in self.list_namespace(namespace) if tag_set & set(e.tags)]

    def search_content(self, namespace: str, query: str) -> list[LongTermEntry]:
        tokens = [t for t in query.lower().split() if len(t) > 2]
        if not tokens:
            return [e for e in self.list_namespace(namespace) if query.lower() in e.value.lower()]
        result = []
        for e in self.list_namespace(namespace):
            val = e.value.lower()
            if any(t in val for t in tokens):
                result.append(e)
        return result

    def clear_namespace(self, namespace: str) -> None:
        self._data.pop(namespace, None)
        self._save()

    def close(self) -> None:
        pass


class SqliteBackend:
    def __init__(self, path: str = "lumina_long_term.db"):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                namespace TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                tags TEXT NOT NULL DEFAULT '[]',
                timestamp REAL NOT NULL,
                ttl REAL,
                PRIMARY KEY (namespace, key)
            )
        """)
        self.conn.commit()

    def _row_to_entry(self, row) -> LongTermEntry:
        return LongTermEntry(
            key=row[1],
            value=row[2],
            namespace=row[0],
            tags=json.loads(row[3]),
            timestamp=row[4],
            ttl=row[5],
        )

    def get(self, namespace: str, key: str) -> LongTermEntry | None:
        cursor = self.conn.execute(
            "SELECT namespace,key,value,tags,timestamp,ttl"
            " FROM memory WHERE namespace=? AND key=?",
            (namespace, key),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        entry = self._row_to_entry(row)
        if entry.is_expired:
            self.delete(namespace, key)
            return None
        return entry

    def put(self, entry: LongTermEntry) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO memory"
            " (namespace,key,value,tags,timestamp,ttl)"
            " VALUES (?,?,?,?,?,?)",
            (entry.namespace, entry.key, entry.value,
             json.dumps(entry.tags), entry.timestamp, entry.ttl),
        )
        self.conn.commit()

    def delete(self, namespace: str, key: str) -> bool:
        cursor = self.conn.execute(
            "DELETE FROM memory WHERE namespace=? AND key=?", (namespace, key)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def list_namespace(self, namespace: str) -> list[LongTermEntry]:
        cursor = self.conn.execute(
            "SELECT namespace,key,value,tags,timestamp,ttl"
            " FROM memory WHERE namespace=?",
            (namespace,),
        )
        return [
            e for e in (self._row_to_entry(r) for r in cursor.fetchall())
            if not e.is_expired
        ]

    def search_tags(self, namespace: str, tags: list[str]) -> list[LongTermEntry]:
        return [
            entry for entry in self.list_namespace(namespace)
            if set(tags) & set(entry.tags)
        ]

    def search_content(self, namespace: str, query: str) -> list[LongTermEntry]:
        tokens = [t for t in query.lower().split() if len(t) > 2]
        if not tokens:
            q = f"%{query}%"
            cursor = self.conn.execute(
                "SELECT namespace,key,value,tags,timestamp,ttl"
                " FROM memory WHERE namespace=? AND value LIKE ?",
                (namespace, q),
            )
            return [
                e for e in (self._row_to_entry(r) for r in cursor.fetchall())
                if not e.is_expired
            ]
        result = []
        for entry in self.list_namespace(namespace):
            val = entry.value.lower()
            if any(t in val for t in tokens):
                result.append(entry)
        return result

    def clear_namespace(self, namespace: str) -> None:
        self.conn.execute("DELETE FROM memory WHERE namespace=?", (namespace,))
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


class LongTermMemory:
    """Persistent key-value memory with namespacing, TTL, and pluggable backends."""

    def __init__(self, backend: LongTermBackend | None = None):
        self.backend = backend or JsonFileBackend()

    def remember(
        self, key: str, value: str,
        namespace: str = "default",
        tags: list[str] | None = None,
        ttl: float | None = None,
    ) -> None:
        entry = LongTermEntry(key=key, value=value, namespace=namespace, tags=tags or [], ttl=ttl)
        self.backend.put(entry)

    def recall(self, key: str, namespace: str = "default") -> str | None:
        entry = self.backend.get(namespace, key)
        return entry.value if entry else None

    def forget(self, key: str, namespace: str = "default") -> bool:
        return self.backend.delete(namespace, key)

    def list(self, namespace: str = "default") -> list[LongTermEntry]:
        return self.backend.list_namespace(namespace)

    def search_by_tags(self, tags: list[str], namespace: str = "default") -> list[LongTermEntry]:
        return self.backend.search_tags(namespace, tags)

    def search_content(self, query: str, namespace: str = "default") -> list[LongTermEntry]:
        return self.backend.search_content(namespace, query)

    def clear(self, namespace: str = "default") -> None:
        self.backend.clear_namespace(namespace)

    def close(self) -> None:
        self.backend.close()
