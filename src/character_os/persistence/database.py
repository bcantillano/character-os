"""SQLite database connection and schema."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from character_os.loader.paths import default_data_dir

SCHEMA = """
CREATE TABLE IF NOT EXISTS emotional_drives (
    character_id TEXT PRIMARY KEY,
    curiosity REAL NOT NULL,
    trust REAL NOT NULL,
    excitement REAL NOT NULL,
    fear REAL NOT NULL,
    confidence REAL NOT NULL,
    energy REAL NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS relationships (
    character_id TEXT NOT NULL,
    entity_id TEXT NOT NULL DEFAULT 'user',
    trust REAL NOT NULL,
    familiarity REAL NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (character_id, entity_id)
);

CREATE TABLE IF NOT EXISTS long_term_memories (
    character_id TEXT NOT NULL,
    memory_id TEXT NOT NULL,
    content TEXT NOT NULL,
    importance REAL NOT NULL DEFAULT 0.5,
    tags TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (character_id, memory_id)
);

CREATE TABLE IF NOT EXISTS archived_memories (
    character_id TEXT NOT NULL,
    memory_id TEXT NOT NULL,
    content TEXT NOT NULL,
    importance REAL NOT NULL,
    tags TEXT NOT NULL DEFAULT '[]',
    archived_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (character_id, memory_id)
);
"""


class Database:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_db_path(default_data_dir())
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    def initialize(self) -> None:
        conn = self.connect()
        conn.executescript(SCHEMA)
        conn.commit()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None


def default_db_path(data_dir: Path) -> Path:
    return data_dir / "character_os.sqlite3"
