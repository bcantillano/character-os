"""Tests for forgetting / archiving low-importance memories."""

from pathlib import Path

from character_os.brain.memory import FORGET_IMPORTANCE_THRESHOLD, MemoryFact, MemoryStore
from character_os.core.types import EmotionalDrives
from character_os.llm.providers.stub import StubProvider
from character_os.persistence.database import Database
from character_os.persistence.store import CharacterPersistence
from character_os.session import CharacterSession


def test_forget_stale_removes_low_importance_facts():
    store = MemoryStore()
    store.add(MemoryFact(id="keep", content="Important deal", importance=0.6))
    store.add(MemoryFact(id="drop", content="Trivial aside", importance=0.01))
    forgotten = store.forget_stale()
    assert [f.id for f in forgotten] == ["drop"]
    assert [f.id for f in store.all()] == ["keep"]


def test_decay_then_forget_archives_in_sqlite(tmp_path: Path):
    db = Database(tmp_path / "test.sqlite3")
    store = CharacterPersistence("captain-redbeard", db=db)
    store.memories.add_fact("captain-redbeard", "Fading rumor", importance=0.03)
    store.memories.add_fact("captain-redbeard", "Solid fact", importance=0.7)

    memory = store.load_memory_store()
    memory.decay_importance(amount=0.02)  # 0.03 -> 0.01
    archived = store.forget_stale_memories(memory)

    assert archived == 1
    active = store.memories.list_facts("captain-redbeard")
    assert len(active) == 1
    assert "Solid fact" in active[0].content
    archived_rows = store.memories.list_archived("captain-redbeard")
    assert len(archived_rows) == 1
    assert "Fading rumor" in archived_rows[0].content
    assert archived_rows[0].importance <= FORGET_IMPORTANCE_THRESHOLD
    store.close()


def test_load_archives_already_stale_facts(tmp_path: Path):
    db = Database(tmp_path / "test.sqlite3")
    store = CharacterPersistence("captain-redbeard", db=db)
    store.memories.add_fact("captain-redbeard", "Already dead", importance=0.0)
    store.memories.add_fact("captain-redbeard", "Still alive", importance=0.5)

    loaded = store.load_memory_store()
    assert len(loaded.all()) == 1
    assert "Still alive" in loaded.all()[0].content
    assert len(store.memories.list_archived("captain-redbeard")) == 1
    store.close()


def test_tick_archives_stale_memories(tmp_path: Path):
    session = CharacterSession(
        llm=StubProvider(),
        persist=True,
        data_dir=tmp_path,
        enable_scheduler=False,
    )
    session.brain.memory.add(
        MemoryFact(id="stale", content="Old gossip", importance=0.015),
        dirty=True,
    )
    session.persistence.persist_runtime(
        session.brain.state.emotional_drives,
        session.brain.state.user_trust,
        session.brain.state.user_familiarity,
        session.brain.memory,
        only_dirty_memories=False,
    )
    session.tick()
    assert session.brain.memory.find_similar("Old gossip") is None
    archived = session.persistence.memories.list_archived("captain-redbeard")
    assert any("Old gossip" in f.content for f in archived)
    session.close()


def test_restore_archived_memory(tmp_path: Path):
    db = Database(tmp_path / "test.sqlite3")
    store = CharacterPersistence("captain-redbeard", db=db)
    store.memories.add_fact("captain-redbeard", "Fading rumor", importance=0.0)
    memory = store.load_memory_store()
    assert len(memory.all()) == 0

    archived = store.list_archived_memories()
    assert len(archived) == 1
    restored = store.restore_archived_memory(archived[0].id)
    assert restored is not None
    assert "Fading rumor" in restored.content
    assert restored.importance >= 0.1
    assert store.list_archived_memories() == []

    reloaded = store.load_memory_store()
    assert any("Fading rumor" in f.content for f in reloaded.all())
    store.close()
