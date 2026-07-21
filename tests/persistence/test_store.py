"""Persistence repository tests."""

from pathlib import Path

from character_os.brain.memory import MemoryFact, MemoryStore
from character_os.core.types import EmotionalDrives
from character_os.persistence.database import Database
from character_os.persistence.store import CharacterPersistence


def test_persistence_round_trip(tmp_path: Path):
    db = Database(tmp_path / "test.sqlite3")
    store = CharacterPersistence("captain-redbeard", db=db)

    drives = EmotionalDrives(curiosity=0.8, trust=0.3, excitement=0.4, fear=0.2, confidence=0.7, energy=0.6)
    memory = MemoryStore()
    memory.add(MemoryFact(id="m1", content="User prefers dark rum", importance=0.7, tags=["preference"]))

    written = store.persist_runtime(drives, trust=0.35, familiarity=0.15, memory=memory)
    assert written == 1
    assert memory.dirty_facts() == []

    loaded_drives = store.load_drives(EmotionalDrives())
    rel = store.load_relationship(0.0, 0.0)
    loaded_memory = store.load_memory_store()

    assert loaded_drives.curiosity == 0.8
    assert rel.trust == 0.35
    assert rel.familiarity == 0.15
    facts = loaded_memory.all()
    assert len(facts) == 1
    assert facts[0].content == "User prefers dark rum"

    store.close()


def test_incremental_persist_skips_clean_facts(tmp_path: Path):
    db = Database(tmp_path / "test.sqlite3")
    store = CharacterPersistence("captain-redbeard", db=db)

    memory = MemoryStore()
    memory.add(MemoryFact(id="m1", content="First fact", importance=0.5), dirty=True)
    memory.add(MemoryFact(id="m2", content="Second fact", importance=0.5), dirty=True)
    assert store.persist_runtime(EmotionalDrives(), 0.2, 0.1, memory) == 2

    # Reload as clean, then only dirty one fact.
    memory = store.load_memory_store()
    assert memory.dirty_facts() == []
    target = memory.find_similar("First fact")
    assert target is not None
    target.importance = 0.9
    memory.mark_dirty(target.id)

    written = store.persist_runtime(EmotionalDrives(energy=0.4), 0.2, 0.1, memory)
    assert written == 1

    reloaded = store.load_memory_store().all()
    by_id = {f.id: f for f in reloaded}
    assert by_id["m1"].importance == 0.9
    assert by_id["m2"].importance == 0.5
    store.close()


def test_persistence_survives_reopen(tmp_path: Path):
    db_path = tmp_path / "test.sqlite3"
    db1 = Database(db_path)
    s1 = CharacterPersistence("captain-redbeard", db=db1)
    s1.remember_fact("Met a stranger at the cove", importance=0.65)
    s1.emotions.save("captain-redbeard", EmotionalDrives(energy=0.9))
    s1.close()

    db2 = Database(db_path)
    s2 = CharacterPersistence("captain-redbeard", db=db2)
    facts = s2.load_memory_store().all()
    drives = s2.load_drives(EmotionalDrives())

    assert len(facts) == 1
    assert "stranger" in facts[0].content
    assert drives.energy == 0.9
    s2.close()


def test_session_persists_across_instances(tmp_path: Path):
    from character_os.llm.providers.stub import StubProvider
    from character_os.session import CharacterSession

    s1 = CharacterSession(
        llm=StubProvider(),
        persist=True,
        data_dir=tmp_path,
        enable_scheduler=False,
    )
    s1.send_message("Tell me about your treasure map.")
    trust_after = s1.brain.state.user_trust
    familiarity_after = s1.brain.state.user_familiarity
    s1.close()

    s2 = CharacterSession(
        llm=StubProvider(),
        persist=True,
        data_dir=tmp_path,
        enable_scheduler=False,
    )
    # Relationship + drives round-trip; curiosity may ease toward baseline between turns.
    assert s2.brain.state.user_trust == trust_after
    assert s2.brain.state.user_familiarity == familiarity_after
    assert s2.brain.state.emotional_drives.curiosity > 0
    assert s2.brain.memory.all() or s2.brain.state.user_familiarity > 0
    s2.close()


def test_reset_character_clears_memories_and_restores_defaults(tmp_path: Path):
    db = Database(tmp_path / "test.sqlite3")
    store = CharacterPersistence("captain-redbeard", db=db)

    memory = MemoryStore()
    memory.add(MemoryFact(id="m1", content="User likes rum", importance=0.8), dirty=True)
    store.persist_runtime(
        EmotionalDrives(curiosity=0.99, energy=0.1),
        trust=0.9,
        familiarity=0.8,
        memory=memory,
    )
    store.archive_memories(
        [MemoryFact(id="m2", content="Old stale fact", importance=0.01, tags=[])]
    )

    defaults = EmotionalDrives(curiosity=0.55, trust=0.2, excitement=0.3, fear=0.2, confidence=0.5, energy=0.6)
    stats = store.reset_character(defaults, trust=0.2, familiarity=0.0)

    assert stats["memories_cleared"] == 1
    assert stats["archived_cleared"] == 1
    assert store.load_memory_store().all() == []
    assert store.list_archived_memories() == []
    loaded = store.load_drives(EmotionalDrives())
    assert loaded.curiosity == 0.55
    assert loaded.energy == 0.6
    rel = store.load_relationship(0.0, 0.0)
    assert rel.trust == 0.2
    assert rel.familiarity == 0.0
    store.close()


def test_session_reset_wipes_runtime_and_sqlite(tmp_path: Path):
    from character_os.llm.providers.stub import StubProvider
    from character_os.session import CharacterSession

    session = CharacterSession(
        character_id="lumen",
        llm=StubProvider(),
        persist=True,
        data_dir=tmp_path,
        enable_scheduler=False,
    )
    session.send_message("My name is Ada and I love flatbread.")
    assert session.brain.conversation.state.recent_turns
    # Force a durable fact so reset has something to clear.
    session.brain.memory.add(
        MemoryFact(id="forced", content="The user's name is Ada", importance=0.9),
        dirty=True,
    )
    session.brain._persist()

    stats = session.reset()
    assert stats["memories_cleared"] >= 1
    assert session.brain.memory.all() == []
    assert session.brain.conversation.state.recent_turns == []
    assert session.brain.state.user_trust == session.character.default_trust
    assert session.brain.state.user_familiarity == session.character.default_familiarity
    assert session.brain.state.emotional_drives == session.character.emotional_drives
    assert session.brain.state.tick_count == 0

    # Durable wipe survives reopen.
    session.close()
    again = CharacterSession(
        character_id="lumen",
        llm=StubProvider(),
        persist=True,
        data_dir=tmp_path,
        enable_scheduler=False,
    )
    assert again.brain.memory.all() == []
    again.close()
