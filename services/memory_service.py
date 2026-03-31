# jarvis/services/memory_service.py
"""Episodic memory backed by SQLite FTS5 — BM25 ranked recall with recency bias."""

import sqlite3
from datetime import datetime, timedelta
from shared.logging_utils import get_logger

log = get_logger("memory")


class MemoryService:
    """FTS5-powered semantic recall and storage for episodic events."""

    def __init__(self, db_conn: sqlite3.Connection) -> None:
        self._conn = db_conn
        self._init_fts()

    # ── schema ───────────────────────────────────────────────────────
    def _init_fts(self) -> None:
        self._conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memory
            USING fts5(
                content,
                timestamp UNINDEXED,
                tags      UNINDEXED,
                tokenize  = 'porter unicode61'
            )
        """)
        self._conn.commit()
        log.info("FTS5 episodic memory table ready")

    # ── recall ───────────────────────────────────────────────────────
    def recall_relevant(self, query: str, limit: int = 5) -> list[str]:
        """Return up to *limit* memory fragments ranked by BM25 relevance
        with a secondary sort on recency (newest first)."""
        try:
            rows = self._conn.execute(
                "SELECT content, timestamp FROM memory "
                "WHERE memory MATCH ? "
                "ORDER BY rank, timestamp DESC "
                "LIMIT ?",
                (query, limit),
            ).fetchall()
            results = [r[0] for r in rows]
            if results:
                log.info("Recalled %d memories for query '%s'", len(results), query[:60])
            return results
        except Exception:
            log.exception("FTS5 recall failed for query '%s'", query[:60])
            return []

    # ── store ────────────────────────────────────────────────────────
    def store_event(self, content: str, tags: str = "general") -> None:
        """Persist an episodic event with timestamp and tags."""
        self._conn.execute(
            "INSERT INTO memory (content, timestamp, tags) VALUES (?, ?, ?)",
            (content, datetime.now().isoformat(), tags),
        )
        self._conn.commit()

    # ── decay / pruning ──────────────────────────────────────────────
    def prune_old(self, days: int = 90) -> int:
        """Delete memory entries older than *days*. Returns count deleted."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        cursor = self._conn.execute(
            "DELETE FROM memory WHERE timestamp < ?", (cutoff,)
        )
        self._conn.commit()
        deleted = cursor.rowcount
        if deleted:
            log.info("Pruned %d memories older than %d days", deleted, days)
        return deleted

    # ── stats ────────────────────────────────────────────────────────
    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM memory").fetchone()
        return row[0] if row else 0
