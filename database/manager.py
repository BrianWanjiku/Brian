# jarvis/database/manager.py
"""SQLite abstraction — separate databases for Tasks and Memory."""

import sqlite3
from datetime import datetime
from pathlib import Path
from shared.config import TASKS_DB_PATH, MEMORY_DB_PATH
from shared.config import BASE_DIR
CREATIVE_DB_PATH = BASE_DIR / "database" / "creative.db"
SYSTEM_DB_PATH = BASE_DIR / "database" / "system.db"
from shared.logging_utils import get_logger

log = get_logger("database")


class DatabaseManager:
    """Thin wrapper around four SQLite stores (tasks, memory, creative, system)."""

    def __init__(
        self,
        tasks_path: Path = TASKS_DB_PATH,
        memory_path: Path = MEMORY_DB_PATH,
        creative_path: Path = CREATIVE_DB_PATH,
        system_path: Path = SYSTEM_DB_PATH,
    ):
        self._tasks_path = tasks_path
        self._memory_path = memory_path
        self._creative_path = creative_path
        self._system_path = system_path
        self._tasks_conn: sqlite3.Connection | None = None
        self._memory_conn: sqlite3.Connection | None = None
        self._creative_conn: sqlite3.Connection | None = None
        self._system_conn: sqlite3.Connection | None = None

    # ── initialisation ───────────────────────────────────────────────
    def init_all(self) -> None:
        self._init_tasks_db()
        self._init_memory_db()
        self._init_creative_db()
        self._init_system_db()
        log.info("Databases initialised (%s, %s, %s, %s)", self._tasks_path, self._memory_path, self._creative_path, self._system_path)

    def _init_tasks_db(self) -> None:
        self._tasks_conn = sqlite3.connect(str(self._tasks_path))
        self._tasks_conn.row_factory = sqlite3.Row
        c = self._tasks_conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                task_desc    TEXT     NOT NULL,
                trigger_time TEXT,
                interval_min INTEGER DEFAULT 0,
                last_run     TEXT,
                status       TEXT     DEFAULT 'pending',
                created_at   TEXT     DEFAULT (datetime('now'))
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_name TEXT    NOT NULL,
                progress  INTEGER DEFAULT 0,
                status    TEXT    DEFAULT 'active',
                created_at TEXT   DEFAULT (datetime('now'))
            )
        """)
        self._tasks_conn.commit()

    def _init_memory_db(self) -> None:
        self._memory_conn = sqlite3.connect(str(self._memory_path))
        self._memory_conn.row_factory = sqlite3.Row
        c = self._memory_conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                role      TEXT NOT NULL,
                content   TEXT NOT NULL,
                timestamp TEXT DEFAULT (datetime('now'))
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                key       TEXT NOT NULL UNIQUE,
                value     TEXT NOT NULL,
                updated   TEXT DEFAULT (datetime('now'))
            )
        """)
        # NOTE: FTS5 'memory' virtual table is created by MemoryService
        self._memory_conn.commit()

    def _init_creative_db(self) -> None:
        self._creative_conn = sqlite3.connect(str(self._creative_path))
        self._creative_conn.row_factory = sqlite3.Row
        c = self._creative_conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS scenarios (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                project   TEXT NOT NULL,
                plan      TEXT NOT NULL,
                alignment INTEGER DEFAULT 0,
                updated   TEXT DEFAULT (datetime('now'))
            )
        """)
        self._creative_conn.commit()

    def _init_system_db(self) -> None:
        self._system_conn = sqlite3.connect(str(self._system_path))
        self._system_conn.row_factory = sqlite3.Row
        c = self._system_conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type  TEXT NOT NULL,
                description TEXT NOT NULL,
                value       INTEGER DEFAULT 0,
                timestamp   TEXT DEFAULT (datetime('now'))
            )
        """)
        self._system_conn.commit()

    # ── connection accessors ─────────────────────────────────────────
    def get_memory_conn(self) -> sqlite3.Connection:
        return self._memory_conn
    
    def get_creative_conn(self) -> sqlite3.Connection:
        return self._creative_conn
        
    def get_system_conn(self) -> sqlite3.Connection:
        return self._system_conn

    # ── Tasks CRUD ───────────────────────────────────────────────────
    def add_task(
        self, desc: str, trigger_time: str | None = None, interval_min: int = 0
    ) -> int:
        c = self._tasks_conn.cursor()
        c.execute(
            "INSERT INTO tasks (task_desc, trigger_time, interval_min) VALUES (?,?,?)",
            (desc, trigger_time, interval_min),
        )
        self._tasks_conn.commit()
        log.info("Task added: %s (id=%d)", desc, c.lastrowid)
        return c.lastrowid

    def get_pending_tasks(self) -> list[dict]:
        now = datetime.utcnow().isoformat()
        c = self._tasks_conn.cursor()
        rows = c.execute(
            "SELECT * FROM tasks WHERE status='pending' AND (trigger_time IS NULL OR trigger_time <= ?)",
            (now,),
        ).fetchall()
        return [dict(r) for r in rows]

    def complete_task(self, task_id: int) -> None:
        now = datetime.utcnow().isoformat()
        self._tasks_conn.execute(
            "UPDATE tasks SET status='done', last_run=? WHERE id=?", (now, task_id)
        )
        self._tasks_conn.commit()

    # ── Goals CRUD ───────────────────────────────────────────────────
    def add_goal(self, name: str) -> int:
        c = self._tasks_conn.cursor()
        c.execute("INSERT INTO goals (goal_name) VALUES (?)", (name,))
        self._tasks_conn.commit()
        return c.lastrowid

    def update_goal(self, goal_id: int, progress: int, status: str = "active") -> None:
        self._tasks_conn.execute(
            "UPDATE goals SET progress=?, status=? WHERE id=?",
            (progress, status, goal_id),
        )
        self._tasks_conn.commit()

    # ── Memory CRUD ──────────────────────────────────────────────────
    def add_memory(self, role: str, content: str) -> None:
        self._memory_conn.execute(
            "INSERT INTO conversations (role, content) VALUES (?,?)", (role, content)
        )
        self._memory_conn.commit()

    def get_recent_conversations(self, limit: int = 20) -> list[dict]:
        rows = self._memory_conn.execute(
            "SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def search_memory(self, query: str) -> list[dict]:
        rows = self._memory_conn.execute(
            "SELECT role, content, timestamp FROM conversations WHERE content LIKE ?",
            (f"%{query}%",),
        ).fetchall()
        return [dict(r) for r in rows]

    def set_fact(self, key: str, value: str) -> None:
        self._memory_conn.execute(
            "INSERT INTO facts (key, value) VALUES (?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated=datetime('now')",
            (key, value),
        )
        self._memory_conn.commit()

    def get_fact(self, key: str) -> str | None:
        row = self._memory_conn.execute(
            "SELECT value FROM facts WHERE key=?", (key,)
        ).fetchone()
        return row["value"] if row else None

    # ── cleanup ──────────────────────────────────────────────────────
    def close(self) -> None:
        for conn in (self._tasks_conn, self._memory_conn, self._creative_conn, self._system_conn):
            if conn:
                conn.close()
        log.info("Database connections closed")
