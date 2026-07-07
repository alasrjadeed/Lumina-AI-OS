from __future__ import annotations

import contextlib
import json
import sqlite3
import threading
from datetime import UTC, datetime
from uuid import UUID

from kernel.events.dead_letter import DeadLetterEntry
from kernel.events.event import Event


class SqliteDeadLetterQueue:
    def __init__(self, db_path: str, max_entries: int = 5000) -> None:
        self._db_path = db_path
        self._max_entries = max_entries
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        with self._lock, sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS dead_letters (
                    id TEXT PRIMARY KEY,
                    event_name TEXT,
                    event_payload TEXT,
                    event_source TEXT,
                    event_correlation_id TEXT,
                    event_version INTEGER DEFAULT 0,
                    event_is_replay INTEGER DEFAULT 0,
                    event_timestamp REAL DEFAULT 0,
                    failed_at TEXT,
                    attempts INTEGER DEFAULT 0,
                    exception TEXT,
                    exception_type TEXT,
                    subscriber TEXT
                )
                """,
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_dlq_failed_at ON dead_letters(failed_at)",
            )

    def add(self, entry: DeadLetterEntry) -> None:
        with self._lock, sqlite3.connect(self._db_path) as conn:
            if self._count(conn) >= self._max_entries:
                conn.execute(
                    "DELETE FROM dead_letters WHERE id IN ("
                    "SELECT id FROM dead_letters ORDER BY failed_at ASC LIMIT ?"
                    ")",
                    (max(1, self._count(conn) - self._max_entries + 1),),
                )
            conn.execute(
                """
                INSERT INTO dead_letters
                    (id, event_name, event_payload, event_source,
                     event_correlation_id, event_version, event_is_replay,
                     event_timestamp, failed_at, attempts, exception,
                     exception_type, subscriber)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._row(entry),
            )

    def count(self) -> int:
        with self._lock, sqlite3.connect(self._db_path) as conn:
            return self._count(conn)

    def _count(self, conn: sqlite3.Connection) -> int:
        row = conn.execute("SELECT COUNT(*) FROM dead_letters").fetchone()
        return row[0] if row else 0

    def latest(self, limit: int = 10) -> list[DeadLetterEntry]:
        with self._lock, sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM dead_letters ORDER BY failed_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [self._entry(r) for r in rows]

    def all(self) -> list[DeadLetterEntry]:
        with self._lock, sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM dead_letters ORDER BY failed_at ASC",
            ).fetchall()
            return [self._entry(r) for r in rows]

    def clear(self) -> None:
        with self._lock, sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM dead_letters")

    @staticmethod
    def _row(entry: DeadLetterEntry) -> tuple:
        return (
            str(entry.id),
            entry.event.name if entry.event else None,
            json.dumps(entry.event.payload)
            if entry.event and entry.event.payload is not None
            else None,
            entry.event.source if entry.event else None,
            entry.event.correlation_id if entry.event else None,
            entry.event.version if entry.event else 0,
            int(entry.event.is_replay) if entry.event else 0,
            entry.event.timestamp if entry.event else 0.0,
            entry.failed_at.isoformat(),
            entry.attempts,
            entry.exception,
            entry.exception_type,
            entry.subscriber,
        )

    @staticmethod
    def _entry(row: sqlite3.Row) -> DeadLetterEntry:
        event: Event | None = None
        if row[1]:
            payload = row[2]
            with contextlib.suppress(json.JSONDecodeError, TypeError):
                payload = json.loads(payload) if payload else None
            event = Event(
                name=row[1],
                payload=payload,
                source=row[3] or "",
                correlation_id=row[4] or "",
                version=row[5] or 0,
                is_replay=bool(row[6]),
                timestamp=row[7] or 0.0,
            )
        failed_at = datetime.fromisoformat(row[8]) if row[8] else datetime.now(UTC)
        return DeadLetterEntry(
            id=UUID(row[0]),
            event=event,
            failed_at=failed_at,
            attempts=row[9] or 0,
            exception=row[10] or "",
            exception_type=row[11] or "",
            subscriber=row[12] or "",
        )
