"""Tests for spoken-memory formatting helpers."""

from character_os.brain.memory import MemoryFact, MemoryStore
from character_os.brain.speech_memory import (
    extract_known_name,
    format_speech_memory_context,
    user_asks_about_memory,
)


def test_extract_known_name():
    facts = [
        MemoryFact(id="1", content="The user's name is Byron", importance=0.7),
        MemoryFact(id="2", content="prefers honest deals", importance=0.6),
    ]
    assert extract_known_name(facts) == "Byron"


def test_user_asks_about_memory():
    assert user_asks_about_memory("Do you remember my name?")
    assert user_asks_about_memory("What's my name?")
    assert not user_asks_about_memory("Where is the treasure?")


def test_speech_memory_context_emphasizes_name_on_recall():
    store = MemoryStore()
    store.add(MemoryFact(id="1", content="The user's name is Byron", importance=0.7))
    text = format_speech_memory_context(store, user_message="Do you remember my name?")
    assert "Their name is Byron" in text
    assert "Do not claim you forgot" in text
    assert "say Byron" in text
