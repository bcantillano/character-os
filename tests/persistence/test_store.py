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

    store.persist_runtime(drives, trust=0.35, familiarity=0.15, memory=memory)

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
    before = s1.brain.state.emotional_drives.curiosity
    s1.send_message("Tell me about your treasure map.")
    s1.close()

    s2 = CharacterSession(
        llm=StubProvider(),
        persist=True,
        data_dir=tmp_path,
        enable_scheduler=False,
    )
    assert s2.brain.state.emotional_drives.curiosity >= before
    assert s2.brain.memory.all() or s2.brain.state.user_familiarity > 0
    s2.close()
