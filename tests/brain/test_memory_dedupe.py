"""Tests for memory canonicalization and dedupe."""

from pathlib import Path

from character_os.brain.memory import (
    MemoryFact,
    MemoryStore,
    canonicalize_fact_content,
    memory_key,
)
from character_os.persistence.database import Database
from character_os.persistence.store import CharacterPersistence


def test_canonicalize_name_variants():
    assert canonicalize_fact_content("name: Byron") == "The user's name is Byron"
    assert canonicalize_fact_content("Name is Byron") == "The user's name is Byron"
    assert memory_key("name: Byron") == memory_key("The user's name is Byron")


def test_pet_name_is_not_user_name():
    """Possessive '…'s name is X' must not become the user's name."""
    pet = "dog's name is Pixel"
    assert canonicalize_fact_content(pet) == pet
    assert memory_key(pet) != memory_key("The user's name is Pixel")
    assert not memory_key(pet).startswith("name:")

    store = MemoryStore()
    store.add(MemoryFact(id="1", content=pet, importance=0.6))
    store.dedupe()
    assert store.all()[0].content == pet


def test_canonicalize_prefers():
    assert canonicalize_fact_content("prefers honest deals over bloodshed") == (
        "The user prefers honest deals over bloodshed"
    )
    assert memory_key("prefers honest deals over bloodshed") == memory_key(
        "The user prefers honest deals over bloodshed"
    )


def test_find_similar_matches_name_variants():
    store = MemoryStore()
    store.add(MemoryFact(id="1", content="name: Byron", importance=0.5))
    found = store.find_similar("The user's name is Byron")
    assert found is not None
    assert found.id == "1"


def test_dedupe_collapses_name_and_preference_dupes():
    store = MemoryStore()
    store.add(MemoryFact(id="a", content="name: Byron", importance=0.5))
    store.add(MemoryFact(id="b", content="The user's name is Byron", importance=0.7))
    store.add(MemoryFact(id="c", content="name: Byron", importance=0.4))
    store.add(MemoryFact(id="d", content="prefers honest deals over bloodshed", importance=0.5))
    store.add(
        MemoryFact(
            id="e",
            content="The user prefers honest deals over bloodshed",
            importance=0.6,
        )
    )

    removed = store.dedupe()
    assert len(removed) == 3
    facts = store.all()
    assert len(facts) == 2
    contents = {f.content for f in facts}
    assert "The user's name is Byron" in contents
    assert "The user prefers honest deals over bloodshed" in contents
    name_fact = next(f for f in facts if "name" in f.content.lower())
    assert name_fact.importance == 0.7


def test_dedupe_collapses_short_family_prefix():
    store = MemoryStore()
    store.add(MemoryFact(id="short", content="Byron has a family", importance=0.5))
    store.add(
        MemoryFact(id="long", content="Byron has a family on Medeira", importance=0.55)
    )
    removed = store.dedupe()
    assert removed == ["short"]
    assert len(store.all()) == 1
    assert "Medeira" in store.all()[0].content


def test_dedupe_collapses_contained_compass_facts():
    store = MemoryStore()
    store.add(MemoryFact(id="short", content="Byron has a special compass", importance=0.5))
    store.add(
        MemoryFact(
            id="long",
            content=(
                "Byron has a special compass he is willing to give as a sign of "
                "trust until they get the map."
            ),
            importance=0.55,
        )
    )
    removed = store.dedupe()
    assert removed == ["short"]
    assert len(store.all()) == 1
    assert "willing to give" in store.all()[0].content


def test_persistence_load_dedupes_sqlite(tmp_path: Path):
    db = Database(tmp_path / "test.sqlite3")
    store = CharacterPersistence("captain-redbeard", db=db)
    store.memories.add_fact("captain-redbeard", "name: Byron", importance=0.5)
    store.memories.add_fact("captain-redbeard", "The user's name is Byron", importance=0.6)
    store.memories.add_fact("captain-redbeard", "name: Byron", importance=0.4)
    store.memories.add_fact(
        "captain-redbeard",
        "prefers honest deals over bloodshed",
        importance=0.5,
    )
    store.memories.add_fact(
        "captain-redbeard",
        "The user prefers honest deals over bloodshed",
        importance=0.5,
    )

    loaded = store.load_memory_store()
    assert len(loaded.all()) == 2
    assert len(store.memories.list_facts("captain-redbeard")) == 2

    # Second load is stable.
    assert store.dedupe_memories() == 0
    store.close()


def test_remember_does_not_recreate_name_dupe(tmp_path: Path):
    from character_os.llm.providers.stub import StubProvider
    from character_os.session import CharacterSession

    session = CharacterSession(
        llm=StubProvider(),
        persist=True,
        data_dir=tmp_path,
        enable_scheduler=False,
    )
    session.brain._remember_notable_facts(["name: Byron"], "My name is Byron")
    session.brain._remember_notable_facts(["The user's name is Byron"], "Do you remember?")
    facts = session.brain.memory.all()
    name_facts = [f for f in facts if "byron" in f.content.lower()]
    assert len(name_facts) == 1
    session.close()
