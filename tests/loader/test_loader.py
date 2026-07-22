"""Loader tests against example content packs."""

from character_os.loader import PromptLoader, load_character, load_world


def test_load_captain_redbeard():
    character = load_character("captain-redbeard")
    assert character.id == "captain-redbeard"
    assert character.world == "caribbean-1790"
    assert character.emotional_drives.curiosity == 0.7
    assert any(g.id == "find_treasure_map" for g in character.goals)
    assert character.knowledge
    assert "response_generator" in character.prompts
    assert "internal_thoughts" in character.prompts
    assert "without grilling" in next(
        g.description for g in character.goals if g.id == "size_up_stranger"
    ).lower()


def test_redbeard_prompt_override_loads():
    loader = PromptLoader()
    character = load_character("captain-redbeard")
    text = loader.load(
        "response_generator",
        override_path=character.prompts["response_generator"],
    )
    assert "default: no question mark" in text.lower()
    assert "banned loops" in text.lower()
    thoughts = loader.load(
        "internal_thoughts",
        override_path=character.prompts["internal_thoughts"],
    )
    assert "text-only" in thoughts.lower()


def test_load_lumen_companion():
    character = load_character("lumen")
    assert character.id == "lumen"
    assert character.name == "Lumen"
    assert character.world == "everyday-present"
    assert character.tts.voice == "cedar"
    assert character.tts.speed == 0.90
    assert character.tts.normalize_speech is False
    assert character.tts.emotion_overlay is True
    assert "lumen" in character.tts.instructions.lower()
    assert "deliberately" in character.tts.instructions.lower()
    assert any(g.id == "understand_people" for g in character.goals)
    assert character.emotional_drives.curiosity == 0.55
    assert character.emotional_drives.excitement < 0.4
    assert "response_generator" in character.prompts
    assert "internal_thoughts" in character.prompts


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
    assert "quiet_corner" in ids
    assert "kitchen_table" in ids


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
            "recent_dialogue": "User: Hello",
        },
    )
    assert "Captain Redbeard" in text
    assert "{{" not in text
    assert "Recent dialogue" in loader.load("response_generator")
    assert "Known facts about this person" in loader.load("response_generator")
    assert "Relationship with this person" in loader.load("response_generator")
    assert "Relationship with this person" in loader.load("internal_thoughts")
    assert "User just said" in loader.load("internal_thoughts")
    assert "Recent dialogue" in loader.load("internal_thoughts")


def test_lumen_prompt_override_loads():
    loader = PromptLoader()
    character = load_character("lumen")
    text = loader.load(
        "response_generator",
        override_path=character.prompts["response_generator"],
    )
    assert "default: no question" in text.lower()
    assert "that sounds like" in text.lower()
    assert "how about" in text.lower()
    assert "current turn wins" in text.lower()
    assert "food lists" in text.lower()
    assert "dark knight" in text.lower()
    assert "### examples" in text.lower()
    thoughts = loader.load(
        "internal_thoughts",
        override_path=character.prompts["internal_thoughts"],
    )
    assert "user just said" in thoughts.lower()
    assert "recent dialogue" in thoughts.lower()
    assert "i wonder" in thoughts.lower()
    assert "protein" in thoughts.lower() or "nutrition" in thoughts.lower()
    goal = next(g for g in character.goals if g.id == "understand_people")
    assert "patterns" not in goal.description.lower()
    assert "what they say now" in goal.description.lower()
