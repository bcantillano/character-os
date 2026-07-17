"""Load and save durable character state (Remember stage)."""

from __future__ import annotations

from pathlib import Path

from character_os.brain.memory import MemoryFact, MemoryStore
from character_os.core.types import CharacterDefinition, EmotionalDrives
from character_os.loader.paths import default_data_dir
from character_os.persistence.database import Database, default_db_path
from character_os.persistence.repositories.emotion import EmotionRepository
from character_os.persistence.repositories.long_term_memory import LongTermMemoryRepository
from character_os.persistence.repositories.relationships import (
    DEFAULT_ENTITY,
    RelationshipRecord,
    RelationshipsRepository,
)


class CharacterPersistence:
    """SQLite-backed long-term state for one character."""

    def __init__(self, character_id: str, db: Database | None = None, data_dir: Path | None = None) -> None:
        if db is None:
            root = data_dir or default_data_dir()
            db = Database(default_db_path(root))
        db.initialize()
        self.character_id = character_id
        self.db = db
        self.memories = LongTermMemoryRepository(db)
        self.emotions = EmotionRepository(db)
        self.relationships = RelationshipsRepository(db)

    def load_memory_store(self) -> MemoryStore:
        store = MemoryStore()
        for fact in self.memories.list_facts(self.character_id):
            store.add(fact, dirty=False)
        self._sync_dedupe(store)
        self._sync_forget(store)
        return store

    def dedupe_memories(self) -> int:
        """Collapse duplicate facts in SQLite. Returns number of rows deleted."""
        store = MemoryStore()
        for fact in self.memories.list_facts(self.character_id):
            store.add(fact, dirty=False)
        return self._sync_dedupe(store)

    def forget_stale_memories(self, memory: MemoryStore | None = None) -> int:
        """Archive active facts at/below importance threshold. Returns count archived."""
        if memory is None:
            memory = MemoryStore()
            for fact in self.memories.list_facts(self.character_id):
                memory.add(fact, dirty=False)
        return self._sync_forget(memory)

    def _sync_dedupe(self, store: MemoryStore) -> int:
        removed = store.dedupe()
        if removed:
            self.memories.delete_many(self.character_id, removed)
        # Persist keepers whose content/importance/tags were upgraded.
        for fact in store.dirty_facts():
            self.memories.upsert(self.character_id, fact)
        store.clear_dirty()
        return len(removed)

    def _sync_forget(self, store: MemoryStore) -> int:
        forgotten = store.forget_stale()
        if forgotten:
            self.memories.archive_facts(self.character_id, forgotten)
        return len(forgotten)

    def archive_memories(self, facts: list[MemoryFact]) -> int:
        """Archive the given facts (already removed from the in-memory store)."""
        return self.memories.archive_facts(self.character_id, facts)

    def list_archived_memories(self) -> list[MemoryFact]:
        return self.memories.list_archived(self.character_id)

    def restore_archived_memory(self, memory_id: str) -> MemoryFact | None:
        """Restore one archived fact into active SQLite memory."""
        return self.memories.restore_archived(self.character_id, memory_id)

    def load_drives(self, fallback: EmotionalDrives) -> EmotionalDrives:
        return self.emotions.load(self.character_id) or fallback

    def load_relationship(self, fallback_trust: float, fallback_familiarity: float) -> RelationshipRecord:
        record = self.relationships.load(self.character_id, DEFAULT_ENTITY)
        if record is None:
            return RelationshipRecord(DEFAULT_ENTITY, fallback_trust, fallback_familiarity)
        return record

    def persist_runtime(
        self,
        drives: EmotionalDrives,
        trust: float,
        familiarity: float,
        memory: MemoryStore,
        *,
        only_dirty_memories: bool = True,
    ) -> int:
        """Persist drives/relationship always; memories only if dirty (default).

        Returns the number of memory rows upserted.
        """
        self.emotions.save(self.character_id, drives)
        self.relationships.save(
            self.character_id,
            RelationshipRecord(DEFAULT_ENTITY, trust, familiarity),
        )
        facts = memory.dirty_facts() if only_dirty_memories else memory.all()
        for fact in facts:
            self.memories.upsert(self.character_id, fact)
        if only_dirty_memories:
            memory.clear_dirty()
        return len(facts)

    def decay_memory_importance(self, amount: float = 0.01) -> None:
        self.memories.decay_importance(self.character_id, amount)

    def remember_fact(self, content: str, *, importance: float = 0.5, tags: list[str] | None = None) -> MemoryFact:
        return self.memories.add_fact(self.character_id, content, importance=importance, tags=tags)

    def close(self) -> None:
        self.db.close()


def create_persistence(
    character: CharacterDefinition,
    data_dir: Path | None = None,
) -> CharacterPersistence:
    return CharacterPersistence(character.id, data_dir=data_dir)
