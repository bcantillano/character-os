"""Long-term memory persistence."""

from __future__ import annotations

import json
from uuid import uuid4

from character_os.brain.memory import MemoryFact
from character_os.persistence.database import Database


class LongTermMemoryRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def list_facts(self, character_id: str) -> list[MemoryFact]:
        conn = self.db.connect()
        rows = conn.execute(
            """
            SELECT memory_id, content, importance, tags
            FROM long_term_memories
            WHERE character_id = ?
            ORDER BY importance DESC
            """,
            (character_id,),
        ).fetchall()
        return [_row_to_fact(row) for row in rows]

    def upsert(self, character_id: str, fact: MemoryFact) -> None:
        conn = self.db.connect()
        conn.execute(
            """
            INSERT INTO long_term_memories (character_id, memory_id, content, importance, tags)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(character_id, memory_id) DO UPDATE SET
                content = excluded.content,
                importance = excluded.importance,
                tags = excluded.tags,
                updated_at = datetime('now')
            """,
            (
                character_id,
                fact.id,
                fact.content,
                fact.importance,
                json.dumps(fact.tags),
            ),
        )
        conn.commit()

    def add_fact(
        self,
        character_id: str,
        content: str,
        *,
        importance: float = 0.5,
        tags: list[str] | None = None,
    ) -> MemoryFact:
        fact = MemoryFact(id=str(uuid4()), content=content, importance=importance, tags=tags or [])
        self.upsert(character_id, fact)
        return fact

    def delete(self, character_id: str, memory_id: str) -> None:
        conn = self.db.connect()
        conn.execute(
            """
            DELETE FROM long_term_memories
            WHERE character_id = ? AND memory_id = ?
            """,
            (character_id, memory_id),
        )
        conn.commit()

    def delete_many(self, character_id: str, memory_ids: list[str]) -> int:
        if not memory_ids:
            return 0
        conn = self.db.connect()
        conn.executemany(
            """
            DELETE FROM long_term_memories
            WHERE character_id = ? AND memory_id = ?
            """,
            [(character_id, mid) for mid in memory_ids],
        )
        conn.commit()
        return len(memory_ids)

    def decay_importance(self, character_id: str, amount: float = 0.01) -> None:
        conn = self.db.connect()
        conn.execute(
            """
            UPDATE long_term_memories
            SET importance = MAX(0.0, importance - ?),
                updated_at = datetime('now')
            WHERE character_id = ?
            """,
            (amount, character_id),
        )
        conn.commit()


def _row_to_fact(row) -> MemoryFact:
    tags = json.loads(row["tags"]) if row["tags"] else []
    return MemoryFact(
        id=row["memory_id"],
        content=row["content"],
        importance=float(row["importance"]),
        tags=tags,
    )
