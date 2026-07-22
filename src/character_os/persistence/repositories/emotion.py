"""Emotional drive persistence."""

from __future__ import annotations

from character_os.core.types import EmotionalDrives
from character_os.persistence.database import Database


class EmotionRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def load(self, character_id: str) -> EmotionalDrives | None:
        conn = self.db.connect()
        row = conn.execute(
            """
            SELECT curiosity, trust, excitement, fear, confidence, energy
            FROM emotional_drives WHERE character_id = ?
            """,
            (character_id,),
        ).fetchone()
        if row is None:
            return None
        return EmotionalDrives(
            curiosity=row["curiosity"],
            trust=row["trust"],
            excitement=row["excitement"],
            fear=row["fear"],
            confidence=row["confidence"],
            energy=row["energy"],
        ).clamp()

    def save(self, character_id: str, drives: EmotionalDrives) -> None:
        d = drives.clamp()
        conn = self.db.connect()
        conn.execute(
            """
            INSERT INTO emotional_drives (
                character_id, curiosity, trust, excitement, fear, confidence, energy
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(character_id) DO UPDATE SET
                curiosity = excluded.curiosity,
                trust = excluded.trust,
                excitement = excluded.excitement,
                fear = excluded.fear,
                confidence = excluded.confidence,
                energy = excluded.energy,
                updated_at = datetime('now')
            """,
            (
                character_id,
                d.curiosity,
                d.trust,
                d.excitement,
                d.fear,
                d.confidence,
                d.energy,
            ),
        )
        conn.commit()

    def delete(self, character_id: str) -> None:
        conn = self.db.connect()
        conn.execute(
            "DELETE FROM emotional_drives WHERE character_id = ?",
            (character_id,),
        )
        conn.commit()
