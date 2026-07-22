"""Relationship persistence (trust / familiarity per entity)."""

from __future__ import annotations

from dataclasses import dataclass

from character_os.persistence.database import Database

DEFAULT_ENTITY = "user"


@dataclass
class RelationshipRecord:
    entity_id: str
    trust: float
    familiarity: float


class RelationshipsRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def load(self, character_id: str, entity_id: str = DEFAULT_ENTITY) -> RelationshipRecord | None:
        conn = self.db.connect()
        row = conn.execute(
            """
            SELECT entity_id, trust, familiarity
            FROM relationships
            WHERE character_id = ? AND entity_id = ?
            """,
            (character_id, entity_id),
        ).fetchone()
        if row is None:
            return None
        return RelationshipRecord(
            entity_id=row["entity_id"],
            trust=float(row["trust"]),
            familiarity=float(row["familiarity"]),
        )

    def save(self, character_id: str, record: RelationshipRecord) -> None:
        conn = self.db.connect()
        conn.execute(
            """
            INSERT INTO relationships (character_id, entity_id, trust, familiarity)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(character_id, entity_id) DO UPDATE SET
                trust = excluded.trust,
                familiarity = excluded.familiarity,
                updated_at = datetime('now')
            """,
            (character_id, record.entity_id, record.trust, record.familiarity),
        )
        conn.commit()

    def delete_all(self, character_id: str) -> None:
        conn = self.db.connect()
        conn.execute(
            "DELETE FROM relationships WHERE character_id = ?",
            (character_id,),
        )
        conn.commit()
