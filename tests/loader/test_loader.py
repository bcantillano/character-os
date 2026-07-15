"""Loader tests against example content packs."""

from character_os.loader import PromptLoader, load_character, load_world


def test_load_captain_redbeard():
    character = load_character("captain-redbeard")
    assert character.id == "captain-redbeard"
    assert character.world == "caribbean-1790"
    assert character.emotional_drives.curiosity == 0.7
    assert any(g.id == "find_treasure_map" for g in character.goals)
    assert character.knowledge


def test_load_caribbean_world():
    world = load_world("caribbean-1790")
    assert world.id == "caribbean-1790"
    ids = {e.id for e in world.knowledge}
    assert "port_royal" in ids
    assert "royal_navy" in ids
    assert "pieces_of_eight" in ids


def test_prompt_render():
    loader = PromptLoader()
    text = loader.load_and_render(
        "response_generator",
        {
            "character_name": "Captain Redbeard",
            "character_description": "A pirate",
            "personality_summary": "bold",
            "emotional_state": "curious",
            "active_goals": "find map",
            "relevant_knowledge": "Port Royal exists",
            "memory_context": "(none)",
            "internal_thoughts": "hmm",
            "user_message": "Hello",
        },
    )
    assert "Captain Redbeard" in text
    assert "{{character_name}}" not in text
