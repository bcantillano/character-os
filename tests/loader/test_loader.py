"""Loader tests against example content packs."""

from character_os.loader import PromptLoader, load_character, load_world


def test_load_captain_redbeard():
    character = load_character("captain-redbeard")
    assert character.id == "captain-redbeard"
    assert character.world == "caribbean-1790"
    assert character.emotional_drives.curiosity == 0.7
    assert any(g.id == "find_treasure_map" for g in character.goals)
    assert character.knowledge


def test_load_lumen_companion():
    character = load_character("lumen")
    assert character.id == "lumen"
    assert character.name == "Lumen"
    assert character.world == "everyday-present"
    assert character.tts.voice == "cedar"
    assert character.tts.speed == 0.88
    assert character.tts.normalize_speech is False
    assert "lumen" in character.tts.instructions.lower()
    assert "deliberately" in character.tts.instructions.lower()
    assert any(g.id == "understand_people" for g in character.goals)
    assert character.emotional_drives.curiosity >= 0.7
    assert character.emotional_drives.excitement < 0.4


def test_load_caribbean_world():
    world = load_world("caribbean-1790")
    assert world.id == "caribbean-1790"
    ids = {e.id for e in world.knowledge}
    assert "port_royal" in ids
    assert "royal_navy" in ids
    assert "pieces_of_eight" in ids


def test_load_everyday_present_world():
    world = load_world("everyday-present")
    assert world.id == "everyday-present"
    ids = {e.id for e in world.knowledge}
    assert "companion_role" in ids
    assert "emotions_as_signals" in ids
    assert "household_presence" in ids


def test_prompt_render():
    loader = PromptLoader()
    text = loader.load_and_render(
        "response_generator",
        {
            "character_name": "Captain Redbeard",
            "character_description": "A pirate",
            "personality_summary": "bold",
            "emotional_state": "curious",
            "relationship_stance": "Building trust (trust=0.45, familiarity=0.40).",
            "active_goals": "find map",
            "memory_context": "(none)",
            "relevant_knowledge": "Port Royal exists",
            "internal_thoughts": "hmm",
            "user_message": "Hello",
        },
    )
    assert "Captain Redbeard" in text
    assert "{{character_name}}" not in text
    assert "{{relationship_stance}}" not in text
    assert "Known facts about this person" in loader.load("response_generator")
    assert "Relationship with this person" in loader.load("response_generator")
    assert "Relationship with this person" in loader.load("internal_thoughts")
